import os
import json

DEFAULT_CONFIG = {
    "include_file_extensions": [
        ".py", ".js", ".html", ".css", ".info", ".http", ".tsx", ".vue", ".mjs", ".rules", ".sh", ".json", ".ts", ".yaml", ".env", ".md", ".jsonl", ".svelte", ".d.ts"
    ],
    "include_tests": False,
    "verbose": False,
}

def get_config():
    return DEFAULT_CONFIG.copy()