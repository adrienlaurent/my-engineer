import os
import time
from anthropic import Anthropic
from .base_provider import LLMProvider
from .utils import get_max_tokens, prepare_messages, log_usage
import json
from datetime import datetime
from pprint import pformat
from rich.console import Console
from .exceptions import OverloadedError
from ...shared_utils.logger import setup_logger


class ClaudeProvider(LLMProvider):
    def __init__(self, run_dir):
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20240620")
        self.max_tokens = get_max_tokens(self.model)
        self.console = Console()
        self.run_dir = run_dir
        self.logger = setup_logger("ClaudeProvider")

    def _prepare_request_data(self, messages, system_prompt=None):
        request_data = self._initialize_request_data(system_prompt)
        processed_messages = self._process_messages(messages)
        request_data["messages"] = processed_messages
        return request_data

    def generate_response(self, messages, system_prompt=None):
        request_data = self._prepare_request_data(messages, system_prompt)
        self._validate_request_data(request_data)
        return self._send_request_and_process_response(request_data)

    def _send_request_and_process_response(self, request_data):
        try:
            self._log_request(request_data)
            response = self._make_api_call(request_data)
            return self._process_response(response, request_data)
        except Exception as e:
            self._handle_error(e)

    def _log_request(self, request_data):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"llm_request_{timestamp}.json"
        log_filepath = os.path.join(self.run_dir, log_filename)
        self.logger.info(f"Run directory: {self.run_dir}")
        self.logger.info(f"Complete LLM request logged to: {log_filepath}")
        self.console.print(f"[bold blue]Complete LLM request logged to: {log_filepath}[/bold blue]")
        with open(log_filepath, 'a') as log_file:
            json.dump(request_data, log_file, indent=2)

    def _make_api_call(self, request_data):
        response = self.client.messages.create(**request_data)
        self.console.print("[bold green]Response received from Claude Sonnet.[/bold green]")
        return response

    def _process_response(self, response, request_data):
        response_data = response.model_dump()
        log_usage(response.usage)
        if not response.content:
            raise ValueError("Received an empty response from Claude")
        return response.content[0].text

    def _handle_error(self, error):
        self.console.print("[bold red]Error while communicating with Claude Sonnet.[/bold red]")
        raise

    def _initialize_request_data(self, system_prompt=None):
        request_data = {
            "model": self.model,
            "extra_headers": {
                "anthropic-beta": "prompt-caching-2024-07-31",
            },
            "max_tokens": self.max_tokens,
            "messages": []
        }
        if system_prompt:
            request_data["system"] = [{"type": "text", "text": system_prompt}]
        return request_data

    def _process_messages(self, messages):
        prepared_messages = prepare_messages(messages)
        if not prepared_messages:
            raise ValueError("No valid messages provided")
        
        return [self._process_single_message(msg, i, len(prepared_messages))
                for i, msg in enumerate(prepared_messages)]

    def _process_single_message(self, msg, index, total_messages):
        content = self._apply_cache_control(msg["content"], index, total_messages)
        return {"role": msg["role"], "content": content}

    def _apply_cache_control(self, message, index, total_messages):
        if index >= total_messages - 4:
            return [{"type": "text", "text": message, "cache_control": {"type": "ephemeral"}}]
        return [{"type": "text", "text": message}]

    def _validate_request_data(self, request_data):
        if not request_data["messages"]:
            raise ValueError("No valid messages after preparation")

    def set_run_dir(self, run_dir):
        self.run_dir = run_dir