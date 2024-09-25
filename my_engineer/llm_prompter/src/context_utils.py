import os
import sys
from pathlib import Path
from ...codebase_concatenator import concatenate_codebase_to_string
from ...shared_utils.logger import setup_logger
from ...context_management.smart_context_builder import SmartContextBuilder
from ...shared_utils.file_utils import get_app_root

logger = setup_logger(__name__)

def get_current_dir():
    """Get the current working directory."""
    return os.getcwd()

def read_requirements():
    try:
        current_dir = get_current_dir()
        requirements_path = os.path.join(current_dir, "requirements.txt")
        with open(requirements_path, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        logger.warning(
            "requirements.txt not found in the current directory. Proceeding without requirements."
        )
        return "Requirements file not found"
    except Exception as e:
        logger.error(f"Error reading requirements.txt: {str(e)}")
        return f"Error reading requirements: {str(e)}"

def get_context(include_tests: bool, user_request: str, run_dir: str) -> str:
    
    assert user_request != ''

    logger.info(f"Run dir: {run_dir}")
    smart_context = ""
    try:
        app_root = get_app_root()
        current_dir = get_current_dir()
        logger.info(f"MY-ENGINEER Application root: {app_root}")
        logger.info(f"Current directory: {current_dir}")
        content = ""
        
        smart_context_builder = SmartContextBuilder(current_dir, run_dir)
        smart_context, relevant_files = smart_context_builder.build_smart_context(user_request)
        logger.info(f"Generated smart context based on user request. Relevant files: {relevant_files}")
        content += "\n\n*** SMART CONTEXT ***\n\n" + smart_context
        logger.info("Smart context added to the overall context")

        try:
            standards_path = os.path.join(app_root, "templates/coding-standards.yaml")
            with open(standards_path, "r", encoding="utf-8") as standards_file:
                content += "\n\n*** CODING STANDARDS ***\n\n" + standards_file.read()
        except FileNotFoundError:
            logger.warning(
                "coding-standards.yaml not found in the current directory. Proceeding without coding standards context."
            )
            raise

        pythonpath = os.environ.get("PYTHONPATH", "Not set")
        content += f"\n\n*** PYTHONPATH ***\n{pythonpath}\n"

        content += f"\n\n*** REQUIREMENTS ***\n{read_requirements()}\n"

        try:
            instructions_path = os.path.join(app_root, "templates/instructions.txt")
            with open(instructions_path, "r", encoding="utf-8") as instructions_file:
                content += "\n\n*** INSTRUCTIONS ***\n\n" + instructions_file.read()
        except FileNotFoundError:
            logger.warning(
                "instructions.txt not found in the current directory. Proceeding without instructions context."
            )

        with open(os.path.join(run_dir, "initial_context_final_content.txt"), "w", encoding="utf-8") as file:
            file.write(content)
        logger.info(f"Concatenated content saved to initial_context_final_content.txt")

        return content
        
    except Exception as e:
        logger.error(f"Error generating context: {str(e)}")
        raise

def read_requirements():
    try:
        with open(os.path.join(get_app_root(), "requirements.txt"), "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError as e:
        logger.warning(f"Requirements file not found: {str(e)}")
        return "Requirements file not found"
    except Exception as e:
        logger.error(f"Error reading requirements file: {str(e)}")
        return f"Error reading requirements: {str(e)}"

app_root = get_app_root()
logger.info(f"MY ENGINEER Application root: {app_root}")