import os
from .concatenator import CodebaseConcatenator
from .config import DEFAULT_CONFIG
from ..shared_utils.logger import setup_logger

def concatenate_codebase_to_string(**kwargs):
    """
    Concatenate codebase to a string.
    """
    logger = setup_logger("codebase_concatenator")
    config = DEFAULT_CONFIG.copy()
    config.update(kwargs)
    logger.info(f"Starting concatenation from root directory: {config.get('root_dir', os.getcwd())}")
    logger.info(f"Include file extensions: {', '.join(config['include_file_extensions'])}")
    logger.info(f"Include tests: {config.get('include_tests', False)}")
    try:
        concatenator = CodebaseConcatenator(**config)
        return concatenator.concat_files()
    except Exception as error:
        logger.error(f"Critical Error: {str(error)}")
        return ""