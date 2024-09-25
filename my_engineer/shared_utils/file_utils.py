import os
import re
import subprocess
from typing import List
import mimetypes
from ..shared_utils.logger import setup_logger
from anthropic import Anthropic
from .pipeline_helpers import get_editor_command

logger = setup_logger(__name__)

def empty_file(file_path: str) -> None:
    """
    Empties the contents of a file.

    Args:
        file_path (str): The path to the file to be emptied.

    Raises:
        FileNotFoundError: If the file does not exist.
        PermissionError: If there are insufficient permissions to modify the file.
    """
    try:
        with open(file_path, 'w') as file:
            file.write('')
        logger.info(f"File {file_path} has been emptied.")
    except FileNotFoundError:
        logger.error(f"File {file_path} not found.")
        raise
    except PermissionError:
        logger.error(f"Insufficient permissions to modify {file_path}.")
        raise
    except Exception as e:
        logger.error(f"An error occurred while emptying {file_path}: {str(e)}")
        raise

def ensure_directory_exists(directory_path: str) -> None:
    """
    Ensures that the specified directory exists, creating it if necessary.
    Args:
        directory_path (str): The path of the directory to ensure exists.
    """
    try:
        os.makedirs(directory_path, exist_ok=True)
        logger.info(f"Ensured directory exists: {directory_path}")
    except Exception as e:
        logger.error(f"Error ensuring directory exists {directory_path}: {str(e)}")
        raise

def get_app_root():
    """Get the root directory of the application."""
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    while not os.path.exists(os.path.join(current_dir, 'main.py')):
        parent = os.path.dirname(current_dir)
        if parent == current_dir:
            raise RuntimeError("Could not find application root")
        current_dir = parent
    return current_dir

def get_git_tracked_files(root_dir: str) -> List[str]:
    logger.info(f"Getting git-tracked text files from: {root_dir}")
    if not os.path.isdir(root_dir):
        logger.error(f"Root directory does not exist: {root_dir}")
        return []
    try:
        result = subprocess.run(
            ['git', 'ls-files', '--cached', '--others', '--exclude-standard'],
            capture_output=True, text=True, check=True, cwd=root_dir
        )
        all_files = [os.path.join(root_dir, file) for file in result.stdout.splitlines()]
        
        text_files = []
        for file_path in all_files:
            if is_text_file(file_path) and not file_path.endswith(('package-lock.json', '.svg', '.jpg', '.jpeg', '.png', '.gif')):
                text_files.append(file_path)
        
        logger.info(f"Found {len(text_files)} text files out of {len(all_files)} git-tracked files")
        return text_files
    except subprocess.CalledProcessError as e:
        logger.warning(f"Error running git ls-files: {e}. Falling back to manual file listing.")
        return _manual_file_listing(root_dir)

def is_text_file(file_path: str) -> bool:
    """
    Check if a file is a text file using the 'file' command.
    """
    try:
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type and mime_type.startswith('text'):
            return True
        
        result = subprocess.run(['file', '--mime-type', '-b', file_path], capture_output=True, text=True)
        return result.stdout.strip().startswith('text')
    except subprocess.CalledProcessError:
        # If 'file' command fails, fallback to checking if the file is readable as text
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                f.read(1024)  # Try to read the first 1024 bytes
            return True
        except UnicodeDecodeError:
            return False

def _manual_file_listing(root_dir: str) -> List[str]:
    return [os.path.join(root, file) for root, _, files in os.walk(root_dir) for file in files if is_text_file(os.path.join(root, file))]

def count_tokens(text):
    client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    token_count = client.count_tokens(text)
    return token_count

def count_tokens_for_git_tracked_files():
    """
    Count tokens for all git-tracked files and log the results.
    """
    logger.info("Counting tokens for git-tracked files...")
    working_dir = os.getcwd()
    git_tracked_files = get_git_tracked_files(working_dir)
    total_tokens = 0
    processed_files = 0
    
    for file_path in git_tracked_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            token_count = count_tokens(content)
            total_tokens += token_count
            processed_files += 1
            relative_path = os.path.relpath(file_path, working_dir)
            logger.info(f"File: {relative_path} - Tokens: {token_count:,}")
        except Exception as e:
            logger.error(f"Error counting tokens for {file_path}: {str(e)}")
    
    logger.info(f"Token counting completed. Total tokens: {total_tokens:,} in {processed_files} files.")

def open_file_in_editor(file_path: str):
    """
    Open a file in the configured editor (VS Code or Cursor).
    """
    editor_command = get_editor_command()
    try:
        subprocess.run([editor_command, file_path])
    except Exception as e:
        logger.error(f"Error opening file {file_path} in editor: {str(e)}")