import os
import ast, astor
import datetime
from typing import Dict, List, Optional, Tuple, Union
from itertools import groupby
import subprocess
from difflib import SequenceMatcher
from datetime import datetime
import yaml
import fnmatch
from ..shared_utils.logger import setup_logger
from ..shared_utils.file_utils import ensure_directory_exists, empty_file, get_git_tracked_files
from ..shared_utils.user_input import get_user_approval, InputType
from ..codebase_concatenator import CodebaseConcatenator, get_config
from ..codebase_concatenator.concatenator import CodebaseConcatenator
from ..shared_utils.project_summarizer import ProjectSummarizer
from ..llm_providers import get_provider
from ..llm_providers.providers.exceptions import OverloadedError
from rich.console import Console
from anthropic import Anthropic

Declaration = Tuple[str, str]  # (type, name)

class SmartContextBuilder:
    def __init__(self, root_dir: str, run_dir: str, **kwargs):
        self.config = {}
        self.config.update(kwargs)
        self.root_dir = root_dir
        self.run_dir = run_dir
        self.logger = setup_logger("SmartContextBuilder")
        self._llm_provider = get_provider('haiku', run_dir=self.run_dir)
        self._file_declarations = {}
        self.console = Console()
        config = get_config()
        self.anthropic_client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        config['root_dir'] = self.root_dir
        self._codebase_concatenator = CodebaseConcatenator(**config)
        self._project_summarizer = ProjectSummarizer(self.root_dir, self._llm_provider)
        self.logger.info(f"Created CodebaseConcatenator instance for root_dir: {self.root_dir}")
        self.always_include_patterns = self._load_always_include_patterns()

    def _load_always_include_patterns(self):
        patterns = []
        patterns_file = os.path.join(self.root_dir, 'always_include_patterns.txt')
        try:
            with open(patterns_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        patterns.append(line)
            self.logger.info(f"Loaded {len(patterns)} patterns from {patterns_file}")
        except FileNotFoundError:
            self.logger.warning(f"Always include patterns file not found: {patterns_file}")
        except Exception as e:
            self.logger.error(f"Error reading always include patterns file: {str(e)}")
        return patterns

    def _filter_always_include_files(self, files):
        always_include_files = []
        for pattern in self.always_include_patterns:
            for file in files:
                if fnmatch.fnmatch(file, pattern):
                    always_include_files.append(file)
        return list(set(always_include_files))  # Remove duplicates

    def _merge_file_lists(self, llm_selected_files, always_include_files):
        merged_files = list(set(llm_selected_files + always_include_files))
        merged_files.sort()  # Sort alphabetically
        return merged_files

    def _log_file_selection(self, llm_selected_files, always_include_files, merged_files):
        self.logger.info(f"LLM selected {len(llm_selected_files)} files")
        self.logger.info(f"Always include patterns matched {len(always_include_files)} files")
        self.logger.info(f"Total unique files after merging: {len(merged_files)}")

        # Sort the merged files alphabetically before logging
        for file in sorted(merged_files):
            source = []
            if file in llm_selected_files: source.append("LLM")
            if file in always_include_files: source.append("Always Include")
            self.logger.info(f"{file} - Source: {', '.join(source)}")

    def build_smart_context(self, user_request: str) -> Tuple[str, List[str]]:
        self.logger.info("Building smart context")
        files_to_process = self._get_git_tracked_files()
        self.logger.info(f"Total number of files: {len(files_to_process)}")
        self._extract_declarations(files_to_process)
        self._save_declarations_to_file()
        llm_selected_files = self._select_relevant_files_with_llm(files_to_process, user_request)
        always_include_files = self._filter_always_include_files(files_to_process)
        merged_files = self._merge_file_lists(llm_selected_files, always_include_files)

        self._log_file_selection(llm_selected_files, always_include_files, merged_files)

        use_all_files = False
        total_tokens = 0
        if not llm_selected_files:
            self.logger.info("No relevant files were selected by the LLM.")
            use_all_files = self._ask_user_validation([], len(files_to_process))
        
        if use_all_files:
            self.logger.info("Using all files.")
            relevant_files = files_to_process
            total_tokens = self._count_tokens_for_files(relevant_files)
        elif llm_selected_files:
            self.logger.info("Using LLM selected files.")
            if self._ask_user_validation(merged_files, len(files_to_process)):
                relevant_files = merged_files
                total_tokens = self._count_tokens_for_files(merged_files)
            else:
                relevant_files = files_to_process
                total_tokens = self._count_tokens_for_files(relevant_files)
        
        self.logger.info(f"Total token count for selected files: {total_tokens}")
        self.console.print(f"[bold cyan]Total token count for selected files: {total_tokens}[/bold cyan]")
        
        context = self._build_context(relevant_files)
        self._save_final_context(context)
        return context, relevant_files

    def _get_git_tracked_files(self) -> List[str]:
        return get_git_tracked_files(self.root_dir)

    def _ask_user_validation(self, selected_files, total_files_count):
        if len(selected_files) == 0:
            self.console.print("\nNo files were selected as relevant.")
            self.logger.info("No files were selected as relevant.")
            return get_user_approval("\nDo you want to include all files in the context? (Yes/No)", InputType.GENERAL)
        total_tokens = self._count_tokens_for_files(selected_files)
        self.console.print("\nThe following files have been selected as relevant:")
        # Sort the selected files alphabetically before displaying
        for file in sorted(selected_files):
            self.console.print(f"- {file}", markup=False)
        self.console.print(f"\nTotal files: {total_files_count}")
        self.console.print(f"Selected files: {len(selected_files)}")
        self.console.print(f"Total token count for selected files: {total_tokens}")
        return get_user_approval("\nDo you want to include only these selected files in the context? if no all files will be included", InputType.GENERAL)

    def _count_tokens_for_files(self, file_list: List[str]) -> int:
        total_tokens = 0
        for file_path in file_list:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            tokens = self.anthropic_client.count_tokens(content)
            total_tokens += tokens
        return total_tokens

    def _extract_declarations(self, files: List[str]):
        self.logger.info("Extracting declarations from files")
        for file_path in files:
            try:
                relative_path = os.path.relpath(file_path, self.root_dir)
                if declarations := self._extract_file_declarations(relative_path):
                    self._file_declarations[relative_path] = declarations
            except Exception as e:
                self.logger.error(f"Error processing file {file_path}: {str(e)}")

    def _select_relevant_files_with_llm(self, files: List[str], user_request: str) -> List[str]:
        self._project_summarizer.update_summaries()
        self.logger.info("Selecting relevant files using LLM")
        declarations_context = self._format_declarations_for_llm()
        summary_context = self._project_summarizer.format_summary_for_llm()
        prompt = f"""Given the following project summary, file declarations, and a user request, select the most relevant files for the context:

Project Summary:
{summary_context}

File Declarations:
{declarations_context}

User Request: "{user_request}"

Return ONLY a comma-separated list of file names (not full paths) that are most relevant to the user request. Do not return anything else than the list of files.

Make sure to include any file that is relevant or potentially relevant, or loosly related to the user request. It's better to select more files than less.

IF we need file from a module in src/modules/, includes 100% of all the files in this module.



"""
        response = self._llm_provider.generate_response([{"role": "user", "content": prompt}])
        self.logger.info(f"LLM response for file selection: {response}")
        response_files = [file.strip() for file in response.split(',')]

        relevant_files = list(set([
            file for file in files 
            if any(resp_file in file for resp_file in response_files) and os.path.exists(file)
        ]))
        
        self.logger.debug(f"Files to process: {files}")
        self.logger.debug(f"LLM suggested files: {response_files}")
        self.logger.debug(f"Matched files: {relevant_files}")
        
        # Sort relevant_files alphabetically before logging
        self.logger.info(f"LLM selected {len(relevant_files)} files out of {len(files)} total files:")
        self.logger.info(f"Selected {len(relevant_files)} relevant files: {relevant_files}")
        self._save_llm_conversation(prompt, response, relevant_files)
        return relevant_files

    def _save_llm_conversation(self, prompt: str, response: str, relevant_files: List[str]):
        """Save the LLM conversation to a file in the run directory."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        conversation_file = os.path.join(self.run_dir, f"llm_conversation_{timestamp}.txt")
        try:
            with open(conversation_file, 'w') as f:
                f.write("LLM Request:\n")
                f.write(prompt)
                f.write("\n\nLLM Response:\n")
                f.write(response)
                f.write("\n\nParsed Relevant Files:\n")
                # Sort the relevant files alphabetically before writing
                f.write(", ".join(sorted(os.path.basename(file) for file in relevant_files)))
            self.logger.info(f"Saved LLM conversation to {conversation_file}")
        except Exception as e:
            self.logger.error(f"Error saving LLM conversation to file: {str(e)}")

    def _format_declarations_for_llm(self) -> str:
        formatted_declarations = []
        for file, declarations in self._file_declarations.items():
            file_info = [f"File: {file}"]
            for decl_type, decl_name in declarations[1:]:  # Skip the first FILE declaration
                if decl_type != "FILE":  # Exclude redundant FILE declarations
                    file_info.append(f"{decl_type}: {decl_name}")
            file_info = "\n".join(file_info)
            formatted_declarations.append(file_info)
        return "\n\n".join(formatted_declarations)

    def _save_declarations_to_file(self):
        declarations_file = os.path.join(self.run_dir, "declarations.txt")
        formatted_declarations = self._format_declarations_for_llm()
        try:
            os.makedirs(os.path.dirname(declarations_file), exist_ok=True)
            with open(declarations_file, 'w') as f:
                f.write(formatted_declarations)
            self.logger.info(f"Saved declarations to {declarations_file}")
        except Exception as e:
            self.logger.error(f"Error saving declarations to file: {str(e)}")

    def _build_context(self, relevant_files: List[str]) -> str:
        if not relevant_files:
            self.logger.info("No relevant files to build context.")
            return ""
        return self._codebase_concatenator.concat_files(file_list=relevant_files)

    def _save_final_context(self, context: str) -> None:
        """Save the final context to a file in the run directory."""
        context_file = os.path.join(self.run_dir, "smart_context.txt")
        os.makedirs(os.path.dirname(context_file), exist_ok=True)
        with open(context_file, 'w') as f:
            self.logger.info(f"Writing context to file: {context_file}")
            f.write(context)
        self.logger.info(f"Saved final context to {context_file}")

    def _extract_file_declarations(self, file_path: str) -> List[Tuple[str, str]]:
        declarations = [("FILE", file_path)]

        if file_path.endswith('.py'):
            try:
                with open(os.path.join(self.root_dir, file_path), 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                tree = ast.parse(content)
                
                def visit_node(node):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        declarations.append((type(node).__name__, node.name))
                    elif isinstance(node, ast.ClassDef):
                        declarations.append((type(node).__name__, node.name))
                        for item in node.body:
                            if isinstance(item, ast.FunctionDef):
                                declarations.append(("FunctionDef", item.name))
                
                for node in tree.body:
                    visit_node(node)
            except Exception as e:
                self.logger.error(f"Error extracting declarations from {file_path}: {str(e)}")

        self.logger.info(f"Extracted {len(declarations)} declarations from {file_path}")
        return declarations