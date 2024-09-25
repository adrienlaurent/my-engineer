import io
import os
from typing import List
from .file_utils import FileUtils
from .config import DEFAULT_CONFIG
from ..shared_utils.file_utils import get_git_tracked_files
from ..shared_utils.logger import setup_logger

class CodebaseConcatenator:
    def __init__(self, **kwargs):
        self.config = DEFAULT_CONFIG.copy()
        self.config.update(kwargs)
        self.output_stream = io.StringIO()
        self.processed_files = []
        self.root_dir = self.config.get('root_dir', os.getcwd())
        self.file_utils = FileUtils()
        self.logger = setup_logger("CodebaseConcatenator")
        self.logger.info("CodebaseConcatenator initialized")

    def concat_files(self, file_list=None):
        files_to_process = file_list if file_list is not None else get_git_tracked_files(self.root_dir)
        self._write_header()
        for file_path in files_to_process:
            full_path = os.path.join(self.root_dir, file_path) if not os.path.isabs(file_path) else file_path
            if self._should_process_file(full_path):
                self._write_file_content(full_path)
                self.processed_files.append(full_path)
        self._write_file_list()
        self.logger.info(f"Processed {len(self.processed_files)} files")
        return self.output_stream.getvalue()

    def get_files_to_concatenate(self, file_list=None):
        """
        Returns a list of files that would be included in the concatenation.
        This method can be used by other parts of the code to get the list of files
        without actually performing the concatenation.
        """
        files_to_process = file_list if file_list is not None else get_git_tracked_files(self.root_dir)
        files_to_concatenate = [
            file_path for file_path in files_to_process
            if self._should_process_file(
                os.path.join(self.root_dir, file_path) if not os.path.isabs(file_path) else file_path
            )
        ]
        return list(set(files_to_concatenate))  # Remove duplicates

    def _should_process_file(self, file_path):
        is_test = 'test' in os.path.relpath(file_path, self.root_dir).lower()
        return (not is_test or self.config.get('include_tests', False)) and (
            any(file_path.endswith(ext) for ext in self.config['include_file_extensions']) and not file_path.endswith('package-lock.json')
        )

    def _write_header(self):
        header = "This file contains my whole source code (excluding tests) concatenated into a single txt file. " \
                 "Comments and import have been excluded from the dump to save space. " \
                 "Each file is separated by ###.\n\n"
        self.output_stream.write(header)

    def _write_file_content(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()
            filtered_content = self.file_utils.filter_content(content, file_path)
            relative_path = os.path.relpath(file_path, self.root_dir).replace('\\', '/')  # Ensure forward slashes
            self.output_stream.write(f"\n\n###FILENAME: {relative_path}\n")
            self.output_stream.write(filtered_content)
            if not filtered_content.endswith('\n'):
                self.output_stream.write('\n')
            self.output_stream.write("###END\n")
        except Exception as e:
            self.logger.error(f"Error processing file {file_path}: {str(e)}")

    def _write_file_list(self):
        file_list = "\n\n###FILES PROCESSED:\n"
        for file_path in self.processed_files:
            line_count = sum(1 for _ in open(file_path, 'r', encoding='utf-8', errors='ignore'))
            relative_path = os.path.relpath(file_path, self.root_dir).replace('\\', '/')
            file_list += f"{relative_path} ({line_count} lines)\n"
        self.output_stream.write(file_list)