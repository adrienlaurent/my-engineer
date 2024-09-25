import sys

def is_running_tests():
    """
    Check if the code is currently running as part of a test suite.
    
    Returns:
        bool: True if running tests, False otherwise.
    """
    return 'pytest' in sys.modules