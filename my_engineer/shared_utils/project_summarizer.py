import os
import yaml
from typing import Dict, List
from ..shared_utils.file_utils import get_git_tracked_files
from ..shared_utils.logger import setup_logger

class ProjectSummarizer:
    def __init__(self, root_dir: str, haiku_provider):
        self.root_dir = root_dir
        self.summary_file = os.path.join(root_dir, "file_summaries.yaml")
        self.haiku_provider = haiku_provider
        self.logger = setup_logger("ProjectSummarizer")
        self.summaries = self._load_summaries()

    def _load_summaries(self) -> Dict[str, str]:
        if os.path.exists(self.summary_file):
            with open(self.summary_file, 'r') as f:
                return yaml.safe_load(f) or {}
        self.logger.info("No existing summary file found. Starting with empty summaries.")
        return {}

    def _save_summaries(self):
        with open(self.summary_file, 'w') as f:
            yaml.dump(self.summaries, f)

    def update_summaries(self):
        existing_files = set(self.summaries.keys())
        current_files = set(get_git_tracked_files(self.root_dir))

        new_files = current_files - existing_files
        removed_files = existing_files - current_files

        for file in new_files:
            summary = self._generate_summary(file)
            if summary:
                self.logger.info(f"Generated summary for new file: {file}")
                self.summaries[file] = self.sanitize_for_yaml(summary)

        for file in removed_files:
            del self.summaries[file]

        if new_files or removed_files:
            self._save_summaries()

        self.logger.info(f"Added summaries for {len(new_files)} new files.")
        self.logger.info(f"Removed summaries for {len(removed_files)} deleted files.")

    def _generate_summary(self, file_path: str) -> str:
        try:
            with open(file_path, 'r') as file:
                content = file.read(20000)  # Read first 20,000 characters
            prompt = f"Summarize what this file does in 5 lines or less, list internal dependencies: {file_path}\n\nContent:\n{content}"
            summary = self.haiku_provider.generate_response([{"role": "user", "content": prompt}])
            self.logger.debug(f"Generated summary for {file_path}: {summary[:50]}...")
            return summary.strip()
        except Exception as e:
            self.logger.error(f"Error generating summary for {file_path}: {str(e)}")
            return ""

    def get_summary(self, file_path: str) -> str:
        return self.summaries.get(file_path, "")

    def get_all_summaries(self) -> Dict[str, str]:
        return self.summaries

    def format_summary_for_llm(self) -> str:
        summary_content = ""
        for file_path, summary in self.summaries.items():
            if summary.strip():
                summary_content += f"{file_path}:\n{summary.strip()}\n\n"
        self.logger.debug(f"Formatted summary for LLM: {summary_content[:100]}...")
        return summary_content.strip()

    @staticmethod
    def sanitize_for_yaml(text: str) -> str:
        text = text.replace("'", '"')
        text = text.replace('"', '\\"')
        text = text.replace(': ', '\\: ')
        return text