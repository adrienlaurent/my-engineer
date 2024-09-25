from typing import List, Tuple
from .llm_response_models import PatchInstruction, NewFileInstruction, BashScriptInstruction
from .instruction_parser import InstructionParser

class InstructionProcessor:
    @staticmethod
    def process_instructions(instructions: List[Tuple[str, str, List[str]]]) -> Tuple[List[PatchInstruction], List[NewFileInstruction], List[BashScriptInstruction]]:
        patches = []
        new_files = []
        bash_scripts = []

        for instruction_type, file_path, content in instructions:
            content = '\n'.join(content).strip()
            content = InstructionParser.strip_code_block(content)

            if instruction_type == 'patch':
                patches.append(PatchInstruction(file_path=file_path, patch_content=content))
            elif instruction_type == 'new':
                new_files.append(NewFileInstruction(file_path=file_path, content=content))
            elif instruction_type == 'bash':
                bash_scripts.append(BashScriptInstruction(script_name=file_path, script_content=content))

        return patches, new_files, bash_scripts