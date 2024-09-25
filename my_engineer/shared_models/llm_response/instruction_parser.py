import re
from typing import List, Tuple, Optional

class InstructionParser:
    @staticmethod
    def extract_instructions(text: str) -> Tuple[List[Tuple[str, str, List[str]]], Optional[str], Optional[str], Optional[str]]:
        instructions = []
        preamble = []
        postamble = []
        commit_name = None

        # Regular expression for commit name
        commit_pattern = r'###COMMIT\s*:?\s*(.+)'
        commit_match = re.search(commit_pattern, text)
        if commit_match:
            commit_name = commit_match.group(1).strip()

        # Regular expression for file actions and code blocks
        block_pattern = r'###(\w+):\s*(\S+)\s*```(?:.*?)\n(.*?)```'
        
        # Find all blocks
        block_matches = list(re.finditer(block_pattern, text, re.DOTALL))
        
        if not block_matches:
            # If no blocks found, treat the entire input as preamble
            return [], text.strip(), None, commit_name

        # Process preamble (content before the first block)
        if block_matches[0].start() > 0:
            preamble = text[:block_matches[0].start()].strip()

        # Process blocks
        for match in block_matches:
            action, path, content = match.groups()
            instructions.append((action.lower(), path, InstructionParser._process_content(content)))

        # Process postamble (content after the last block)
        if block_matches[-1].end() < len(text):
            postamble = text[block_matches[-1].end():].strip()

        return instructions, preamble or None, postamble or None, commit_name

    @staticmethod
    def _process_content(content: str) -> List[str]:
        # Remove any leading/trailing empty lines
        lines = content.split('\n')
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()
        return lines

    @staticmethod
    def strip_code_block(content: str) -> str:
        lines = content.split('\n')
        if lines and lines[0].strip() == '```':
            lines = lines[1:]
        if lines and lines[-1].strip() == '```':
            lines = lines[:-1]
        return '\n'.join(lines).strip()