from typing import Dict, Any

class Config:
    def __init__(self):
        self._config: Dict[str, Any] = {
            'editor': 'vscode',  # Default to VS Code
            'use_cursor': False,
            # Add other configuration options here
        }

    def set(self, key: str, value: Any) -> None:
        self._config[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

    @property
    def use_cursor(self) -> bool:
        return self.get('use_cursor', False)

    @property
    def editor(self) -> str:
        return self.get('editor', 'vscode')

# Global config instance
config = Config()

def get_config() -> Config:
    return config