import argparse
import json
from ..shared_models.llm_response.instruction_parser import InstructionParser
from ..shared_models.llm_response.instruction_processor import InstructionProcessor
from ..shared_models.llm_response.llm_response_models import LLMResponseMetadata, LLMResponseContent, LLMResponse
from ..shared_utils.logger import setup_logger
from ..shared_utils.error_handler import ErrorHandler

def process_instructions(raw_instructions: str, run_dir: str) -> LLMResponse:
    if isinstance(raw_instructions, list):
        raw_instructions = '\n'.join(raw_instructions)
    
    instructions, preamble, postamble, commit_name = InstructionParser.extract_instructions(raw_instructions)
    patches, new_files, bash_scripts = InstructionProcessor.process_instructions(instructions)

    content = [LLMResponseContent(text=raw_instructions, type="text")]
    metadata = LLMResponseMetadata(
        id="generated",
        model="unknown",
        role="assistant",
        type="text",
        usage={}
    )
    
    llm_response = LLMResponse(
        content=content,
        metadata=metadata,
        patches=patches,
        new_files=new_files,
        bash_scripts=bash_scripts,
        preamble_instructions=preamble,
        postamble_instructions=postamble,
        commit_name=commit_name
    )
    
    # You can use run_dir here if needed, for example, to save processed instructions
    return llm_response

def main():
    parser = argparse.ArgumentParser(description="Instruction Processor")
    parser.add_argument("input", help="Raw instruction string from LLM")
    args = parser.parse_args()

    logger = setup_logger("instruction_processor")
    error_handler = ErrorHandler(logger)

    try:
        with open(args.input, 'r') as f:
            raw_instructions = f.read()

        llm_response = process_instructions(raw_instructions, args.input)
        print(json.dumps(llm_response.dict(), indent=2))
    except Exception as e:
        error_handler.handle_exception(e, "processing instructions")

if __name__ == "__main__":
    main()