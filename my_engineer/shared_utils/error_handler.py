import logging

class ErrorHandler:
    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def handle_exception(self, e: Exception, context: str = ""):
        error_message = f"Error in {context}: {str(e)}"
        self.logger.error(error_message)
        return error_message