import os
import json
import subprocess
import shutil
from typing import Dict, Optional, List
from datetime import datetime
from rich.console import Console
from ..shared_utils.logger import setup_logger
from ..shared_utils.git_utils import check_uncommitted_changes
from ..shared_utils.user_input import get_user_approval
from ..conversation_manager import ConversationManager
from ..shared_models.chat_models import ConversationState, Message
from ..shared_utils.error_handler import ErrorHandler
from ..shared_models.chat_models import Message, MessageSequence, ConversationState
from ..shared_utils.test_runner.test_runner import check_test_results
import re
from ..shared_utils.config import get_config
import traceback
from colorama import Fore, Style

logger = setup_logger("pipeline_helpers")

error_handler = ErrorHandler(logger)

def setup_run_directory(previous_run_dir: Optional[str] = None) -> str:
    try:
        timestamp = subprocess.check_output(['date', '+%Y-%m-%d_%H-%M-%S']).decode().strip()
        run_dir = os.path.join("runs", timestamp)
        os.makedirs(run_dir)
        logger.info(f"Created run directory: {run_dir}")
        initial_state = ConversationState(previous_run=previous_run_dir)
        ConversationManager.save_state(run_dir, initial_state)
        return run_dir
    except Exception as e:
        error_handler.handle_exception(e, "setting up run directory")
        raise

def get_editor_command():
    config = get_config()
    if config.use_cursor:
        return '/Applications/Cursor.app/Contents/MacOS/Cursor'
    else:
        return 'code'

def resume_from_file(resume_file: str, run_dir: str) -> Dict:
    logger.info(f"Resuming from file: {resume_file}")
    with open(resume_file, 'r') as f:
        raw_instructions = f.read()
    run_dir_context = {
        'raw_instructions': raw_instructions,
        'run_dir': run_dir
    }
    return run_dir_context

def _get_prompt_template() -> Optional[str]:
    template_path = os.path.join(os.getcwd(), "prompt_template.md")
    if os.path.exists(template_path):
        with open(template_path, 'r') as template_file:
            content = template_file.read()
            return content if content else None
    return None

def append_test_results_to_next_prompt(run_dir: str, test_results: str, next_turn_number: int):
    next_prompt_file = f"prompt_{next_turn_number}.md"
    next_prompt_path = os.path.join(run_dir, next_prompt_file)
    
    # Create the next prompt file if it doesn't exist
    if not os.path.exists(next_prompt_path):
        template_content = _get_prompt_template() or ""
        with open(next_prompt_path, 'w') as f:
            f.write(template_content)
    
    # Append the test results to the next prompt file
    with open(next_prompt_path, 'a') as f:
        f.write(f"\n\n## Failed Test Results\n\n {test_results}")

def get_prompt_content(run_dir: str, conversation_state: ConversationState) -> Optional[str]:
    try:
        prompt_file = f"prompt_{conversation_state.turn_number}.md"
        prompt_path = os.path.join(run_dir, prompt_file)
        if not os.path.exists(prompt_path):
            # Create a new file with the template content if it's not empty
            template_content = _get_prompt_template()
            if template_content:
                with open(prompt_path, 'w') as new_prompt_file:
                    new_prompt_file.write(template_content)
                logger.info(f"Created new prompt file with template: {prompt_path}")
            else:
                open(prompt_path, 'w').close()  # Create an empty file
                logger.info(f"Created new empty prompt file: {prompt_path}")

        print(Fore.CYAN + "Processing will start when you close the file that just opened." + Style.RESET_ALL)
        content = _read_and_edit_file(prompt_path)
        if not content:
            logger.info(f"Prompt file {prompt_file} is empty. Reopening for user input.")
            print(Fore.CYAN + "Processing will start when you close the file that just opened." + Style.RESET_ALL)
            content = _read_and_edit_file(prompt_path)
        return content if content else None
    except Exception as e:
        error_handler.handle_exception(e, "getting prompt content")
        return None

def _read_and_edit_file(file_path: str) -> str:
    try:
        editor_command = get_editor_command()
        subprocess.run([editor_command, '--wait', file_path])
        with open(file_path, 'r') as f:
            return f.read().strip()
    except Exception as e:
        logger.error(f"Error reading and editing file: {str(e)}")
        return ""

def sanitize_branch_name(name: str) -> str:
    # Replace spaces and special characters with underscores
    sanitized = re.sub(r'[^\w-]', '-', name)
    # Remove leading/trailing underscores and convert to lowercase
    return sanitized.strip('_').lower()

def create_git_branch(commit_name: str, run_dir: str):
    try:
        timestamp = os.path.basename(run_dir)
        branch_name = f"{timestamp}_{sanitize_branch_name(commit_name)}"
        if not check_uncommitted_changes():  # This function is from git_utils, keep it as is
            subprocess.run(["git", "checkout", "-b", branch_name], check=True)
            logger.info(f"Successfully created and switched to new branch: {branch_name}")
        else:
            logger.warning("Skipping branch creation due to uncommitted changes.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to create new git branch: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise

def generate_instructions(prompt_content: str, llm_prompter, run_dir: str, conversation_state: ConversationState) -> Dict:
    logger.info("Generating instructions")
    logger.debug(f"Prompt content: {prompt_content[:100]}...")
    logger.debug(f"Smart context: {conversation_state.context[:100] if conversation_state.context else 'Not available'}...")
    logger.info(f"Generate instructions run_dir: {run_dir}")
    logger.info(f"Generate instructions conversation_state.previous_run: {conversation_state.previous_run}")

    raw_instructions = llm_prompter.generate_instructions(conversation_state, prompt_content)
    run_dir_context = {
        'raw_instructions': raw_instructions,
        'run_dir': run_dir
    }
    with open(os.path.join(run_dir, f"raw_instructions_turn_{conversation_state.turn_number}.md"), 'w') as f:
        logger.debug(f"Writing raw instructions to {run_dir}/raw_instructions_turn_{conversation_state.turn_number}.md")
        f.write(raw_instructions)
    logger.info(f"Saved raw instructions to {run_dir}/raw_instructions_turn_{conversation_state.turn_number}.md")
    logger.info("Opening raw instructions in VS Code for review and potential editing")
    editor_command = get_editor_command()
    subprocess.Popen([editor_command, '--wait', os.path.join(run_dir_context['run_dir'], f"raw_instructions_turn_{conversation_state.turn_number}.md")], start_new_session=True)
    with open(os.path.join(run_dir, f"raw_instructions_turn_{conversation_state.turn_number}.md"), 'r') as f:
        edited_instructions = f.read()
    if edited_instructions != raw_instructions:
        logger.info("Raw instructions were edited in VS Code. Using edited version.")
        run_dir_context['raw_instructions'] = edited_instructions
        with open(os.path.join(run_dir, f"raw_instructions_turn_{conversation_state.turn_number}.md"), 'w') as f:
            f.write(edited_instructions)
    logger.debug("Finished generate_instructions")
    return run_dir_context

def resume_from_file(resume_file: str, run_dir: str) -> Dict:
    logger.info(f"Resuming from file: {resume_file}")
    with open(resume_file, 'r') as f:
        raw_instructions = f.read()
    run_dir_context = {
        'raw_instructions': raw_instructions,
        'run_dir': run_dir
    }
    return run_dir_context

def process_instructions(run_dir_context: Dict, instruction_processor) -> Dict:
    logger.info("Processing instructions")
    llm_response = instruction_processor.process(run_dir_context['raw_instructions'])
    run_dir_context['llm_response'] = llm_response
    processed_instructions_path = os.path.join(run_dir_context['run_dir'], "processed_instructions.json")
    with open(processed_instructions_path, 'w') as f:
        json.dump(llm_response.dict(), f, indent=2)
    logger.info(f"Saved processed instructions to {processed_instructions_path}")
    return run_dir_context

def process_patches(run_dir_context: Dict, patch_processor) -> Dict:
    project_root = os.getcwd()
    logger.info(f"Processing patches with project root: {project_root}")
    patch_processor.process_patches(run_dir_context['llm_response'].patches, project_root)
    return run_dir_context

def perform_file_operations(run_dir_context: Dict, file_operator) -> Dict:
    logger.info("Performing file operations")
    project_root = os.getcwd()
    file_operator.create_new_files(run_dir_context['llm_response'].new_files, project_root)
    file_operator.save_bash_scripts(run_dir_context['llm_response'].bash_scripts, project_root)
    return run_dir_context

def resume_from_file(resume_file: str, run_dir: str) -> Dict:
    logger.info(f"Resuming from file: {resume_file}")
    with open(resume_file, 'r') as f:
        raw_instructions = f.read()
    run_dir_context = {
        'raw_instructions': raw_instructions,
        'run_dir': run_dir
    }
    return run_dir_context

def get_current_branch() -> str:
    try:
        result = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"],
                                capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to get current branch: {str(e)}")
        return "unknown"