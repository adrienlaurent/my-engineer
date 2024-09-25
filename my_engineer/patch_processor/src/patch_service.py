import os
import sys
import traceback
from datetime import datetime
import anthropic
from importlib import resources  # For Python 3.7+

HAIKU_TOKEN_LIMIT = 3500
SONNET_TOKEN_LIMIT = 7500

class PatchService:
    def __init__(self, logger, llm_provider, run_dir):
        self.logger = logger
        self.haiku_provider = llm_provider
        self.run_dir = run_dir
        self.sonnet_provider = self._create_sonnet_provider(run_dir)
        self.haiku_prompt = self.load_prompt("haiku_prompt.txt")
        self.sonnet_prompt = self.load_prompt("haiku_prompt.txt")
        self.anthropic_client = anthropic.Client(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    def load_prompt(self, prompt_filename):
        try: 
            return resources.read_text("my_engineer.templates", prompt_filename).strip()
        except FileNotFoundError:
            error_message = f"The file '{prompt_filename}' was not found in the templates directory."
            print(f"Error: {error_message}")
            print("Traceback:")
            traceback.print_exc()
            raise FileNotFoundError(error_message)

    def _create_sonnet_provider(self, run_dir):
        from ...llm_providers import get_provider
        return get_provider('claude', run_dir)

    def _check_token_count(self, text):
        return self.anthropic_client.count_tokens(text)

    def apply_patch(self, original_content, patch_content, file_path):
        token_count = self._check_token_count(original_content)
        
        if token_count <= HAIKU_TOKEN_LIMIT:
            return self._apply_patch_with_model(original_content, patch_content, file_path, self.haiku_provider, self.haiku_prompt, "Haiku")
        elif token_count <= SONNET_TOKEN_LIMIT:
            self.logger.info(f"File {file_path} exceeds Haiku token limit. Using Claude Sonnet.")
            return self._apply_patch_with_model(original_content, patch_content, file_path, self.sonnet_provider, self.sonnet_prompt, "Sonnet")
        else:
            raise ValueError(f"Input file is too big even for Sonnet. Token count: {token_count}, limit: {SONNET_TOKEN_LIMIT}")

    def _apply_patch_with_model(self, original_content, patch_content, file_path, provider, prompt_template, model_name):
        self.logger.info(f"Applying patch to {file_path} using {model_name}")
        prompt = prompt_template.format(original_content=original_content, patch_content=patch_content)
        self.logger.info(f"Sending prompt to {model_name} LLM provider")
        messages = [{"role": "user", "content": prompt}]
        response = provider.generate_response(messages)
        self._store_llm_response(file_path, response, model_name)
        
        lines = response.split('\n')
        start_index = next((i for i, line in enumerate(lines) if line.strip().startswith('```')), -1)
        
        if start_index != -1:
            content_lines = lines[start_index + 1:]
            end_index = next((i for i, line in enumerate(reversed(content_lines)) if line.strip().startswith('```')), -1)
            
            if end_index != -1:
                updated_content = '\n'.join(content_lines[:-end_index-1])
                return updated_content
        
        error_msg = "LLM response does not contain properly formatted updated content"
        self.logger.error(error_msg)
        raise ValueError(error_msg)

    def _store_llm_response(self, file_path, response, model_name):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        save_path = os.path.join(self.run_dir, f"{os.path.basename(file_path)}.{timestamp}.{model_name}.txt")
        with open(save_path, "w") as f:
            f.write(response)
        self.logger.info(f"Saved {model_name} response to: {save_path}")