import subprocess
import os
from ..shared_utils.logger import setup_logger
from ..shared_utils.user_input import get_user_approval

logger = setup_logger("git_utils")

def check_uncommitted_changes():
    try:
        # Get the root directory of the git repository
        repo_root = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], universal_newlines=True).strip()
        # Change to the root directory of the repository
        original_dir = os.getcwd()
        os.chdir(repo_root)
        # Check for uncommitted changes
        result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        # Change back to the original directory
        os.chdir(original_dir)
        if result.stdout.strip():
            logger.warning("Warning: There are uncommitted changes in the repository.")
            return True
        return False
    except subprocess.CalledProcessError:
        logger.warning("Warning: Not in a git repository. Skipping uncommitted changes check.")
        return False

def get_current_branch():
    try:
        result = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"],
                               capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to get current branch: {str(e)}")
        return "unknown"

def merge_current_branch_to_main():
    current_branch = get_current_branch()
    if current_branch != "main" and not check_uncommitted_changes():
        if get_user_approval(f"Current branch is '{current_branch}'. Do you want to merge it into 'main'?"):
            try:
                subprocess.run(["git", "checkout", "main"], check=True)
                subprocess.run(["git", "merge", current_branch], check=True)
                logger.info(f"Successfully merged '{current_branch}' into 'main'")
                return True
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to merge '{current_branch}' into 'main': {str(e)}")
    return False

def is_git_repo():
    try:
        subprocess.check_output(['git', 'rev-parse', '--is-inside-work-tree'], stderr=subprocess.STDOUT)
        return True
    except subprocess.CalledProcessError:
        logger.warning("Not in a git repository.")
        return False