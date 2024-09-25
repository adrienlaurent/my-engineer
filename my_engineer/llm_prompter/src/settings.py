import os
from dotenv import load_dotenv
from typing import Dict

class Settings:
    def __init__(self, env_file: str = '.env'):
        load_dotenv()

    def get(self, key: str, default: str = None) -> str:
        return os.getenv(key, default)

    @property
    def api_keys(self) -> Dict[str, str]:
        return {
            'anthropic': self.get('ANTHROPIC_API_KEY'),
            'openai': self.get('OPENAI_API_KEY'),
        }

    @property
    def models(self) -> Dict[str, str]:
        return {
            'claude': self.get('CLAUDE_MODEL', '"claude-3-5-sonnet-20240620"'),
            'chatgpt': self.get('OPENAI_MODEL', 'gpt-4o'),
        }