from ..shared_models import LLMResponse
from .main import process_instructions

class InstructionProcessor:
    def __init__(self, run_dir: str):
        self.run_dir = run_dir

    def process(self, raw_instructions: str) -> LLMResponse:
        """
        Process raw instructions into an LLMResponse object.

        Args:
            raw_instructions (str): The raw instructions from the LLM.

        Returns:
            LLMResponse: A structured response object.
        """
        return process_instructions(raw_instructions, self.run_dir)