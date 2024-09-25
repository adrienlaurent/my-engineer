import os
from ..shared_models import LLMResponse
from ..shared_utils.logger import setup_logger

class FileOperator:
    def __init__(self, logger=None):
        self.logger = logger or setup_logger("file_operator")

    def create_new_files(self, new_files, project_root):
        """
        Create new files in the project root directory.
        """
        for file in new_files:
            self.logger.info(f"Creating new file: {file.file_path}")
            try:
                full_path = os.path.join(project_root, file.file_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, 'w') as f:
                    f.write(file.content)
                self.logger.info(f"Successfully created new file: {full_path}")
            except Exception as e:
                self.logger.error(f"Error creating new file {file.file_path}: {str(e)}")

    def save_bash_scripts(self, bash_scripts, project_root):
        """
        Save bash scripts to the file system.
        """
        for script in bash_scripts:
            self.logger.info(f"Saving bash script: {script.script_name}")
            try:
                script_path = os.path.join(project_root, "bash_scripts", script.script_name)
                os.makedirs(os.path.dirname(script_path), exist_ok=True)
                with open(script_path, 'w') as f:
                    f.write(script.script_content)
                self.logger.info(f"Successfully saved bash script: {script_path}")
            except Exception as e:
                self.logger.error(f"Error saving bash script {script.script_name}: {str(e)}")