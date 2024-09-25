import os
import json
from datetime import datetime
from anthropic import Anthropic
from .base_provider import LLMProvider
from .utils import prepare_messages, get_max_tokens
from rich.console import Console
from my_engineer.shared_utils.logger import setup_logger

class HaikuProvider(LLMProvider):
    def __init__(self, run_dir=None):
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = "claude-3-haiku-20240307"
        self.max_tokens = get_max_tokens(self.model)
        self.logger = setup_logger("HaikuProvider")
        self.run_dir = run_dir
        self.console = Console()

    def generate_response(self, messages, system_prompt=None):
        prepared_messages = prepare_messages(messages)
        if not prepared_messages:
            raise ValueError("No valid messages provided")

        request_data = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": prepared_messages,
        }
        if system_prompt:
            request_data["system"] = system_prompt

        # Log the request
        self._log_request(request_data)

        try:
            response = self.client.messages.create(**request_data)
            response_data = response.model_dump()
            if not response.content:
                raise ValueError("Received an empty response from Haiku")
            self.console.print("[bold green]Response received from Haiku.[/bold green]")
            return response.content[0].text
        except Exception as e:
            self.console.print("[bold red]Error while communicating with Haiku.[/bold red]")
            raise

    def _log_request(self, request_data):
        if self.run_dir:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_filename = f"haiku_request_{timestamp}.json"
            log_filepath = os.path.join(self.run_dir, log_filename)
            with open(log_filepath, 'w') as log_file:
                json.dump(request_data, log_file, indent=2)
            self.logger.info(f"Complete Haiku request logged to: {log_filepath}")
            self.console.print(f"[bold blue]Complete Haiku request logged to: {log_filepath}[/bold blue]")