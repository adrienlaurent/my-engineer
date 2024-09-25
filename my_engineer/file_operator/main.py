import argparse
import json
import shutil
import os
from src.file_service import FileService
from shared_models import LLMResponse
from shared_utils.logger import setup_logger
from shared_utils.error_handler import ErrorHandler
from colorama import Fore, init

# Initialize colorama
init(autoreset=True)

def main():
    parser = argparse.ArgumentParser(description="File Operator")
    parser.add_argument("--log-level", default="INFO", help="Set the logging level")
    parser.add_argument("input", help="JSON file containing the LLMResponse")
    parser.add_argument("--new-files-dir", help="Directory to store copies of new files", required=True)
    args = parser.parse_args()

    logger = setup_logger("file_operator")
    error_handler = ErrorHandler(logger)
    file_service = FileService(logger)

    try:
        with open(args.input, 'r') as f:
            llm_response_dict = json.load(f)
        llm_response = LLMResponse(**llm_response_dict)

        # Process new files
        if llm_response.new_files:
            print(f"{Fore.YELLOW}New files to be created:{Fore.RESET}")
            for new_file in llm_response.new_files:
                print(f"- {new_file.file_path}")
            user_input = input(f"{Fore.CYAN}Do you want to create these new files? (yes/no): {Fore.RESET}").lower()
            if user_input == 'yes':
                file_service.process_new_files(llm_response.new_files)
                # Copy new files to the specified directory
                for new_file in llm_response.new_files:
                    dest_path = os.path.join(args.new_files_dir, os.path.basename(new_file.file_path))
                    shutil.copy2(new_file.file_path, dest_path)
                    print(f"{Fore.GREEN}Copied new file to: {dest_path}{Fore.RESET}")
            else:
                print(f"{Fore.YELLOW}Skipping new file creation.{Fore.RESET}")

        # Process patches
        if llm_response.patches:
            print(f"{Fore.YELLOW}Patches to be applied:{Fore.RESET}")
            for patch in llm_response.patches:
                print(f"- {patch.file_path}")
            file_service.process_patches(llm_response.patches)

        # Process bash scripts
        if llm_response.bash_scripts:
            for script in llm_response.bash_scripts:
                user_input = input(f"{Fore.CYAN}Do you want to execute the bash script '{script.script_name}'? (yes/no): {Fore.RESET}").lower()
                if user_input == 'yes':
                    file_service.execute_bash_script(script)
                else:
                    print(f"{Fore.YELLOW}Skipping bash script execution for '{script.script_name}'.{Fore.RESET}")

        if llm_response.preamble_instructions:
            print(f"{Fore.GREEN}Preamble instructions:{Fore.RESET}")
            print(llm_response.preamble_instructions)

        if llm_response.postamble_instructions:
            print(f"{Fore.GREEN}Postamble instructions:{Fore.RESET}")
            print(llm_response.postamble_instructions)

        print(f"{Fore.GREEN}File operations completed successfully{Fore.RESET}")

    except Exception as e:
        error_handler.handle_exception(e, "processing file operations")

if __name__ == "__main__":
    main()