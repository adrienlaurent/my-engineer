import os
from .src.patch_service import PatchService
from ..llm_providers import get_provider
from ..shared_utils.logger import setup_logger
import traceback
import filecmp

class PatchProcessor:
    def __init__(self, run_dir):
        logger = setup_logger("patch_processor")
        haiku_provider = get_provider('haiku', run_dir)
        self.__patch_service = PatchService(logger, haiku_provider, run_dir=run_dir)
        self.logger = setup_logger("patch_processor")
        self.run_dir = run_dir

    def apply_patch(self, original_content: str, patch_content: str, file_path: str) -> str:
        """
        Apply a patch to the original content.
        Args:
            original_content (str): The original file content.
            patch_content (str): The patch to apply.
            file_path (str): The path of the file being patched.
        Returns:
            str: The updated file content after applying the patch.
        """
        return self.__patch_service.apply_patch(original_content, patch_content, file_path)

    def process_patches(self, patches, project_root):
        """
        Process and apply patches to the actual project files.
        """
        for patch in patches:
            self.logger.info(f"Processing patch for file: {patch.file_path}")
            try:
                full_path = os.path.join(project_root, patch.file_path)
                
                with open(full_path, 'r') as f:
                    original_content = f.read()
                    original_first_line = original_content.split('\n')[0] if original_content else ""

                try:
                    updated_content = self.apply_patch(original_content, patch.patch_content, patch.file_path)
                except ValueError as e:
                    self.logger.error(f"Error processing patch for {patch.file_path}: {str(e)}.")
                    self.logger.error("Skipping this patch due to file size exceeding maximum token limit.")
                    continue
                except Exception as e:
                    self.logger.error(f"Unexpected error processing patch for {patch.file_path}: {str(e)}")
                    continue
                
                updated_lines = updated_content.split('\n')
                if updated_lines[0] != original_first_line:
                    self.logger.info(f"First line changed in {patch.file_path}")
                    if updated_lines[0].strip() == "":
                        self.logger.warning(f"First line became empty in {patch.file_path}, preserving original")
                        updated_lines[0] = original_first_line
                        updated_content = '\n'.join(updated_lines)

                # Compare the updated content with the original content
                if updated_content != original_content:
                    # Content is different, so we proceed with the update
                    with open(full_path, 'w') as f:
                        f.write(updated_content)
                    self.logger.info(f"Successfully updated file: {full_path}")
                else:
                    # Content is identical, no need to update
                    self.logger.info(f"No changes applied to file: {full_path}")

                patch.processed_patch_path = full_path  # Mark as processed
            except Exception as e:
                self.logger.error(f"Error processing patch for {patch.file_path}: {str(e)}")
                self.logger.error(f"Traceback: {traceback.format_exc()}")