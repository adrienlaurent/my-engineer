from typing import List
from .llm_response_models import LLMResponse, LLMResponseContent, LLMResponseMetadata
from .instruction_parser import InstructionParser
from .instruction_processor import InstructionProcessor

class LLMResponseHandler:
    @staticmethod
    def create_llm_response(content: List[LLMResponseContent], metadata: LLMResponseMetadata) -> LLMResponse:
        response = LLMResponse(content=content, metadata=metadata)
        LLMResponseHandler._parse_instructions(response)
        return response

    @staticmethod
    def _parse_instructions(response: LLMResponse):
        full_text = LLMResponseHandler._get_full_text(response)
        lines = full_text.split('\n')
        for i, line in enumerate(lines):
            lines[i] = line.rstrip()  # Remove trailing whitespace
        instructions, preamble, postamble, commit_name = InstructionParser.extract_instructions(lines)
        patches, new_files, bash_scripts = InstructionProcessor.process_instructions(instructions)
        response.patches = patches
        response.new_files = new_files
        response.bash_scripts = bash_scripts
        response.preamble_instructions = '\n'.join(preamble).strip() if preamble else None
        response.postamble_instructions = '\n'.join(postamble).strip() if postamble else None
        response.commit_name = commit_name

    @staticmethod
    def _get_full_text(response: LLMResponse) -> str:
        return "\n".join(item.text for item in response.content)