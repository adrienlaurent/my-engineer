import os
import sys
from dotenv import load_dotenv
from ..llm_providers import get_provider
from ..shared_utils.logger import setup_logger
from ..shared_utils.file_utils import empty_file, get_app_root
from ..shared_utils.test_runner.test_utils import is_running_tests

class PromptPostProcessor:
    def __init__(self, run_dir=None):
        self.logger = setup_logger("prompt_post_processor")
        self.haiku_provider = get_provider('haiku', run_dir=run_dir)
        self.post_processing_prompt = self._load_post_processing_prompt()
        self.is_test = is_running_tests()
        load_dotenv()
        self.post_process_char_limit = int(os.getenv('POST_PROCESS_CHAR_LIMIT', 100000))

    def _load_post_processing_prompt(self):
        prompt_file = os.path.join(get_app_root(), "templates/post_processing_prompt.txt")
        try:
            with open(prompt_file, 'r') as f:
                return f.read().strip()
        except FileNotFoundError:
            self.logger.error(f"Post-processing prompt file '{prompt_file}' not found.")
            return ""

    def post_process(self, original_prompt: str, run_dir: str) -> str:
        if len(original_prompt) <= self.post_process_char_limit:
            self.logger.info(f"Original prompt is less than {self.post_process_char_limit} characters. Skipping post-processing.")
            return original_prompt
        if not self.post_processing_prompt:
            self.logger.warning("Post-processing prompt is empty. Skipping post-processing.")
            return original_prompt
        self.logger.info("Post-processing prompt")
        try:
            messages = [
                {"role": "user", "content": f"{self.post_processing_prompt}\n\n{original_prompt}"}
            ]
            post_processed_prompt = self.haiku_provider.generate_response(messages)
            post_processed_file = os.path.join(run_dir, "post_processed_prompt.md")
            with open(post_processed_file, 'w') as f:
                f.write(post_processed_prompt)
            self.logger.info(f"Post-processed prompt saved to {post_processed_file}")
            return post_processed_file
        except Exception as e:
            self.logger.error(f"Error during prompt post-processing: {str(e)}")
            return original_prompt

    def is_test_environment(self):
        return 'PYTEST_CURRENT_TEST' in os.environ

    def get_final_prompt(self, original_prompt: str, post_processed_file: str, turn_number: int, run_dir: str) -> str:
        try:
            with open(post_processed_file, 'r') as f:
                post_processed_prompt = f.read()
            self._save_post_processed_prompt(post_processed_prompt, turn_number, run_dir)
            return post_processed_prompt
        except FileNotFoundError:
            self.logger.warning(f"Post-processed file not found: {post_processed_file}. Returning original prompt.")
            return original_prompt

    def _save_post_processed_prompt(self, post_processed_prompt: str, turn_number: int, run_dir: str):
        file_name = f"post_processed_prompt_turn_{turn_number}.md"
        file_path = os.path.join(run_dir, file_name)
        with open(file_path, 'w') as f:
            f.write(post_processed_prompt)
        self.logger.info(f"Saved post-processed prompt for turn {turn_number} to {file_path}")