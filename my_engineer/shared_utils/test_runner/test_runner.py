import subprocess
import os
from ...shared_utils.logger import setup_logger
from typing import Optional
import logging
import json

def run_unit_tests() -> str:
    """
    Run pytest for unit tests from the current working directory and return the results as a string.
    """
    try:
        output = ""
        current_dir = os.getcwd()
        venv_activate = os.path.join(current_dir, '.venv', 'bin', 'activate')
        pytest_ini_path = os.path.join(current_dir, 'pytest.ini')
        
        if not os.path.exists(venv_activate):
            logger.warning(f"Virtual environment not found at {venv_activate}.")
        
        if not os.path.exists(pytest_ini_path):
            logger.warning(f"pytest.ini not found at {pytest_ini_path}. Skipping tests.")
            return "Tests skipped: pytest.ini not found."
        
        logger.info(f"Running pytest in directory: {current_dir}")
        command = f"source {venv_activate} && pytest --disable-warnings"
        result = subprocess.run(
            command,
            shell=True,
            executable='/bin/bash',
            cwd=current_dir,
            capture_output=True,
            text=True,
            check=False  # Don't raise an exception for test failures
        )
        output = result.stdout + result.stderr
        logger.info("Pytest execution completed")
        
        return output
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running pytest: {str(e)}")
        return f"Error running pytest: {str(e)}"
    except FileNotFoundError:
        logger.error("Pytest not found. Make sure it's installed in your environment.")
        return "Pytest not found. Make sure it's installed in your environment."
    except Exception as e:
        logger.error(f"Unexpected error running pytest: {str(e)}")
        return f"Unexpected error running pytest: {str(e)}"

def check_test_results(output: str) -> bool:
    """
    Check if all tests passed based on pytest output.
    """
    if output.startswith("Tests skipped:"):
        return True
    if "errors during collection" in output:
        return False
    if "failed" in output.lower():
        return False
    if "error" in output.lower():
        return False
    return "passed" in output.lower()

def get_first_failed_test(output: str) -> Optional[str]:
    """
    Extract the name of the first failed test from pytest output.
    """
    lines = output.split('\n')
    for line in lines:
        if "ERROR collecting" in line:
            return line.split("ERROR collecting")[-1].strip()
    for line in lines:
        if line.startswith("FAILED "):
            return line.split("::")[1].split()[0]
    return None

# Set up logger
from ...shared_utils.logger import setup_logger
logger = setup_logger(__name__)