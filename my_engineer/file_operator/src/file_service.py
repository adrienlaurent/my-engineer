import os
import shutil
from shared_utils.logger import setup_logger
from shared_models import PatchInstruction, NewFileInstruction, BashScriptInstruction
from colorama import Fore, init

# Initialize colorama
init(autoreset=True)

class FileService:
    def __init__(self, logger):
        self.logger = logger
        self.run_dir = None
        self.new_files_dir = None
        self.patches_dir = None

    def set_run_directory(self, run_dir):
        self.run_dir = run_dir
        self.new_files_dir = os.path.join(run_dir, "new_files")
        self.patches_dir = os.path.join(run_dir, "patches")
        os.makedirs(self.new_files_dir, exist_ok=True)
        os.makedirs(self.patches_dir, exist_ok=True)

    def process_new_files(self, new_files: list[NewFileInstruction]):
        self.logger.info(f"Processing {len(new_files)} new files")
        for new_file in new_files:
            self.create_new_file(new_file)

    def create_new_file(self, new_file: NewFileInstruction):
        self.logger.info(f"Creating new file: {new_file.file_path}")
        staged_path = os.path.join(self.new_files_dir or '', os.path.basename(new_file.file_path))
        try:
            os.makedirs(os.path.dirname(staged_path), exist_ok=True)
            with open(staged_path, 'w') as f:
                f.write(new_file.content)
            self.logger.info(f"Successfully created new file: {staged_path}")
        except Exception as e:
            self.logger.error(f"Error creating new file {new_file.file_path}: {str(e)}")
            raise

    def process_patches(self, patches: list[PatchInstruction]):
        self.logger.info(f"Processing {len(patches)} patches")
        for patch in patches:
            self.stage_patch(patch)

    def stage_patch(self, patch: PatchInstruction):
        self.logger.info(f"Staging patch for file: {patch.file_path}")
        try:
            diff_file_name = f"{os.path.basename(patch.file_path)}.diff"
            diff_file_path = os.path.join(self.patches_dir or '', diff_file_name)
            os.makedirs(self.patches_dir, exist_ok=True)
            with open(diff_file_path, 'w') as f:
                f.write(f"Original file: {patch.file_path}\n")
                f.write("```diff\n")
                f.write(patch.patch_content)
                f.write("\n```\n")
            self.logger.info(f"Successfully staged patch: {diff_file_path}")
            # Update the patch instruction with the staged path
            patch.processed_patch_path = diff_file_path
        except Exception as e:
            self.logger.error(f"Error staging patch for {patch.file_path}: {str(e)}")
            raise

    def process_new_files(self, new_files: list[NewFileInstruction]):
        self.logger.info(f"Processing {len(new_files)} new files")
        for new_file in new_files:
            self.create_new_file(new_file)

    def process_llm_response(self, llm_response):
        self.logger.info("Processing LLM response")
        if llm_response.new_files:
            self.process_new_files(llm_response.new_files)
        if llm_response.patches:
            self.process_patches(llm_response.patches)
        for bash_script in llm_response.bash_scripts:
            self.execute_bash_script(bash_script)
        self.logger.info("Finished processing LLM response")