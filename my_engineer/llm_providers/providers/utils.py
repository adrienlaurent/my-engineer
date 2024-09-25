import json
from typing import Dict
import os
from rich.console import Console

MODEL_MAX_TOKENS = {
    "claude-3-haiku-20240307": 4096,
    "claude-3-5-sonnet-20240620": 8192
}

def get_max_tokens(model):
    return MODEL_MAX_TOKENS.get(model, 4096)

def prepare_messages(messages):
    prepared_messages = []
    for message in messages:
        if message["role"] in ["user", "assistant"] and message["content"].strip():
            if not prepared_messages or prepared_messages[-1]["role"] != message["role"]:
                prepared_messages.append(message)
            else:
                prepared_messages[-1]["content"] += "\n" + message["content"]
    return prepared_messages

def log_usage(usage_info):
    usage_data = {
        "input_tokens": getattr(usage_info, 'input_tokens', 0),
        "output_tokens": getattr(usage_info, 'output_tokens', 0),
        "total_tokens": getattr(usage_info, 'input_tokens', 0) + getattr(usage_info, 'output_tokens', 0),
        "cache_creation_input_tokens": getattr(usage_info, 'cache_creation_input_tokens', 0),
        "cache_read_input_tokens": getattr(usage_info, 'cache_read_input_tokens', 0)
    }
    print(f"Claude Usage: {json.dumps(usage_data, indent=2)}")

def log_llm_request(model: str):
    console = Console()
    console.print(f"[bold blue]Sending request to LLM model: {model}[/bold blue]")

class Settings:
    def __init__(self, env_file: str = '.env'):
        self.env_file = env_file

    def get(self, key: str, default: str = None) -> str:
        return os.getenv(key, default)

    @property
    def api_keys(self) -> Dict[str, str]:
        return {
            'anthropic': self.get('ANTHROPIC_API_KEY'),
            'openai': self.get('OPENAI_API_KEY'),
        }