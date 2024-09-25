from .claude_provider import ClaudeProvider
from .haiku_provider import HaikuProvider

def get_provider(provider_name: str, run_dir: str):
    if provider_name.lower() == "claude":
        return ClaudeProvider(run_dir=run_dir)
    elif provider_name.lower() == "haiku":
        return HaikuProvider(run_dir=run_dir)
    else:
        raise ValueError(f"Unknown provider: {provider_name}")