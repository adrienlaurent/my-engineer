import os
import re
import subprocess
from typing import List
import mimetypes
import chardet
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

def get_git_tracked_files(repo_path: str) -> List[str]:
    try:
        result = subprocess.run(
            ['git', '-C', repo_path, 'ls-files', '--cached', '--others', '--exclude-standard'],
            capture_output=True, text=True, check=True
        )
        files = result.stdout.splitlines()
        
        excluded_files = ('package-lock.json', '.svg', '.jpg', '.jpeg', '.png', '.gif', 'file_summaries.yaml')
        excluded_folders = ('.venv', 'runs', 'node_modules')
        
        filtered_files = []
        for file in files:
            full_path = os.path.join(repo_path, file)
            if (not file.endswith(excluded_files) and
                not any(folder in file.split(os.path.sep) for folder in excluded_folders) and
                is_text_file(full_path)):
                filtered_files.append(full_path)
        
        logger.info(f"Found {len(filtered_files)} text files out of {len(files)} git-tracked and untracked files")
        return filtered_files
    except subprocess.CalledProcessError as e:
        logger.error(f"Error getting git-tracked files: {e}")
        return []

def is_text_file(file_path: str, max_bytes: int = 8000) -> bool:
    """
    Determine if a file is a text file by checking its MIME type and content.
    
    Args:
    file_path (str): Path to the file to check
    max_bytes (int): Maximum number of bytes to read for content analysis
    
    Returns:
    bool: True if the file is likely a text file, False otherwise
    """
    # Check file extension first
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type and mime_type.startswith('text'):
        return True
    
    # If mime type is not conclusive, check file content
    try:
        with open(file_path, 'rb') as file:
            raw_data = file.read(max_bytes)
        if not raw_data:
            return False
        
        result = chardet.detect(raw_data)
        if result['encoding'] is not None:
            # Try decoding the content
            try:
                raw_data.decode(result['encoding'])
                return True
            except UnicodeDecodeError:
                return False
        else:
            # If no encoding detected, it's likely not a text file
            return False
    except IOError:
        # If we can't read the file, assume it's not a text file
        return False

def _manual_file_listing(root_dir: str) -> List[str]:
    excluded_folders = ['.venv', 'runs', 'node_modules']
    excluded_files = ['file_summaries.yaml', 'package-lock.json']
    text_files = []
    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in excluded_folders]
        for file in files:
            if file not in excluded_files:
                file_path = os.path.join(root, file)
                if is_text_file(file_path) and not file_path.endswith(('.svg', '.jpg', '.jpeg', '.png', '.gif')):
                    text_files.append(file_path)
    return text_files

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