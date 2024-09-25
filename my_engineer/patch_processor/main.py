import argparse
import json
import os
import hashlib
from src.patch_service import PatchService
from llm_providers import get_provider
from shared_utils.logger import setup_logger
from shared_utils.error_handler import ErrorHandler
from shared_models import LLMResponse

def generate_unique_filename(original_filename, patch_content):
    # Create a hash of the patch content to ensure uniqueness
    content_hash = hashlib.md5(patch_content.encode()).hexdigest()[:8]
    base_name, ext = os.path.splitext(original_filename)
    return f"{base_name}_{content_hash}{ext}.processed"

def main():
    parser = argparse.ArgumentParser(description="Patch Processor")
    parser.add_argument("--log-level", default="INFO", help="Set the logging level")
    parser.add_argument("input_file", help="Path to the LLM response JSON file")
    parser.add_argument("output_dir", help="Directory to store processed patches")
    args = parser.parse_args()

    logger = setup_logger("patch_processor")
    error_handler = ErrorHandler(logger)
    haiku_provider = get_provider('haiku')
    patch_service = PatchService(logger, haiku_provider)

    try:
        with open(args.input_file, 'r') as f:
            llm_response_dict = json.load(f)
        llm_response = LLMResponse(**llm_response_dict)

        os.makedirs(args.output_dir, exist_ok=True)

        for i, patch in enumerate(llm_response.patches):
            logger.info(f"Processing patch {i+1}/{len(llm_response.patches)}")
            # Read the original file content
            try:
                with open(patch.file_path, 'r') as f:
                    original_content = f.read()
            except FileNotFoundError:
                original_content = ""  # If file doesn't exist, use empty string

            updated_content = patch_service.apply_patch(original_content, patch.patch_content)

            # Generate a unique filename for the processed patch
            original_file_name = os.path.basename(patch.file_path)
            unique_filename = generate_unique_filename(original_file_name, patch.patch_content)
            processed_patch_path = os.path.join(args.output_dir, unique_filename)

            # Write the processed patch to a file
            with open(processed_patch_path, 'w') as f:
                f.write(updated_content)

            # Update the patch instruction with the processed patch path
            patch.processed_patch_path = processed_patch_path

        # Write the updated LLM response back to the file
        with open(args.input_file, 'w') as f:
            json.dump(llm_response.dict(), f, indent=2)

        logger.info(f"All patches processed. Updated LLM response written to {args.input_file}")
    except Exception as e:
        error_handler.handle_exception(e, "processing patches")

if __name__ == "__main__":
    main()