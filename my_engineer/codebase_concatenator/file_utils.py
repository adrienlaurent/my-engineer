import os
import re
from ..shared_utils.logger import setup_logger
from ..shared_utils.file_utils import get_git_tracked_files

class FileUtils:
    def __init__(self):
        self.logger = setup_logger("FileUtils")

    @staticmethod
    def get_all_files(dir_path):
        logger = setup_logger("FileUtils")
        logger.info(f"Scanning directory: {dir_path}")
        return get_git_tracked_files(dir_path)

    @staticmethod
    def filter_content(text, file_path):
        if os.path.basename(file_path) == '.env':
            return re.sub(r'^(\w+)=.*$', r'\1=REDACTED', text, flags=re.MULTILINE).strip()
        lines = text.splitlines()
        filtered_lines = [line for line in lines if not line.lstrip().startswith('#') and line.strip()]
        return '\n'.join(filtered_lines)