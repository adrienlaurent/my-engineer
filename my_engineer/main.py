import os
import sys
import json
from typing import Dict, Optional, Tuple
from .llm_prompter.llm_prompter import LLMPrompter
from .instruction_processor.instruction_processor import InstructionProcessor
from .patch_processor.patch_processor import PatchProcessor
from .file_operator.file_operator import FileOperator
from .shared_utils.test_runner.test_runner import run_unit_tests
from .shared_utils.git_utils import check_uncommitted_changes, merge_current_branch_to_main, is_git_repo
from .shared_utils.pipeline_helpers import (
    setup_run_directory, get_prompt_content, create_git_branch, generate_instructions,
    process_instructions, process_patches, perform_file_operations, resume_from_file,
    append_test_results_to_next_prompt, check_test_results, get_editor_command
)
from .shared_utils.file_utils import count_tokens_for_git_tracked_files, get_git_tracked_files
from .shared_utils.auto_test_fixer import auto_fix_tests
from .shared_utils.user_input import get_user_approval, InputType
from .shared_utils.logger import setup_logger, get_log_file_path
from .shared_utils.file_utils import empty_file
from .conversation_manager import ConversationManager
from .conversation_manager.conversation_manager import PydanticEncoder
from .shared_models.chat_models import ConversationState, Message
from .prompt_post_processor import PromptPostProcessor
from .llm_prompter.src.context_utils import get_context
import argparse
from .shared_utils.config import get_config
from rich.console import Console
from colorama import Fore, Style, init
import traceback
import subprocess
import signal
import sys
from dotenv import load_dotenv, set_key

load_dotenv()

# Add the project root to sys.path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

LOG_LEVEL = os.environ.get('LOGLEVEL', 'DEBUG').upper()
console = Console()
logger = setup_logger("main")
logger.setLevel(LOG_LEVEL)

parser = argparse.ArgumentParser(description="My Engineer")
parser.add_argument("--prompt-file", help="Path to the prompt file (optional)")
parser.add_argument("--resume", help="Path to an existing run directory to resume from")
parser.add_argument("--use-cursor", action="store_true", help="Use Cursor instead of VS Code as the editor")
parser.add_argument("--include-tests", action="store_true", help="WIP - Include the tests file")
parser.add_argument("--auto-fix-tests", action="store_true", help="WIP - Automatically attempt to fix failing tests (requires --include-tests)")
args = parser.parse_args()

def signal_handler(signum, frame):
    logger.info("Received interrupt signal. Exiting gracefully...")
    print(f"\n{Fore.YELLOW}Process interrupted. Exiting gracefully...{Style.RESET_ALL}")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def my_engineer_pipeline(prompt_file: Optional[str], include_tests: bool = False, resume: Optional[str] = None, use_cursor: bool = False):
    config = get_config()
    config.set('use_cursor', use_cursor)
    editor_command = get_editor_command()
    logger.info(f"Starting My Engineer pipeline")
    run_dir = setup_run_directory(prompt_file)
    logger.info(f"Log level set to: {LOG_LEVEL}")
    logger.info(f"Current run directory: {run_dir}")

    llm_prompter = LLMPrompter(run_dir=run_dir)
    instruction_processor = InstructionProcessor(run_dir=run_dir)

    if resume:
        # Extract the run directory from the resume file path
        run_dir = os.path.dirname(os.path.abspath(resume))
        logger.info(f"Resuming with run directory: {run_dir}")

    patch_processor = PatchProcessor(run_dir=run_dir)
    file_operator = FileOperator(logger)
    prompt_post_processor = PromptPostProcessor()
    run_dir_context = {'run_dir': run_dir}

    if check_uncommitted_changes():
        if not get_user_approval("There are uncommitted changes in the current branch. Do you want to continue?"):
            logger.warning("Pipeline execution cancelled by user due to uncommitted changes.")
            return None

    if merge_current_branch_to_main():
        return None

    try:
        working_dir = os.getcwd()
        logger.info(f"Current working directory: {working_dir}")
        config = get_config()
        config.set('use_cursor', args.use_cursor)
        logger.info(f"Use Cursor setting: {config.use_cursor}")
        conversation_state = ConversationManager.load_state(run_dir) or ConversationState.from_dict({})
        conversation_state.turn_number = 0
        logger.info(f"Conversation state previous_run: {conversation_state.previous_run}")
        while True:
            if resume:
                console.print("[bold green]Resuming from existing instructions...")
                run_dir_context = resume_from_file(resume, run_dir)
                resume = None  # Reset resume so we don't keep using it in subsequent iterations
            else:
                conversation_state.turn_number += 1
                prompt_content = get_prompt_content(run_dir, conversation_state)
                if prompt_content is None:
                    logger.info("No prompt content provided. Exiting pipeline.")
                    console.print("[yellow]Pipeline execution cancelled due to empty prompt.[/yellow]")
                    return None
                if 'run_dir' in run_dir_context:
                    post_processed_file = prompt_post_processor.post_process(prompt_content, run_dir_context['run_dir'])
                    if post_processed_file and post_processed_file != prompt_content:
                        console.print("[bold green]Prompt has been post-processed. Opening both original and post-processed prompts for review.[/bold green]")
                        subprocess.run([editor_command, '--diff', os.path.join(run_dir_context['run_dir'], f"prompt_{conversation_state.turn_number}.md"), post_processed_file])
                        if get_user_approval("Do you want to use the post-processed prompt? (Y/n)"):
                            prompt_content = prompt_post_processor.get_final_prompt(prompt_content, post_processed_file, conversation_state.turn_number, run_dir)
                        else:
                            logger.info("User chose to use the original prompt.")
                    else:
                        logger.info("Prompt was not post-processed (no changes made during post-processing).")
                logger.info("Generating instructions based on smart context and user prompt")
                run_dir_context = generate_instructions(prompt_content, llm_prompter, run_dir, conversation_state)
                prompt_file_path = os.path.join(run_dir, "prompt_from_command_line.txt")
            console.print("[bold green]Processing instructions...")
            run_dir_context = process_instructions(run_dir_context, instruction_processor)
            logger.debug("Finished processing instructions")
            if run_dir_context['llm_response'].commit_name:
                console.print(f"[bold green]Creating new git branch: {run_dir_context['llm_response'].commit_name}...")
                if not check_uncommitted_changes():
                    create_git_branch(run_dir_context['llm_response'].commit_name, run_dir)
                    empty_file("CHANGELOG.md")
                else:
                    logger.warning("Skipping branch creation due to uncommitted changes.")
            else:
                logger.warning("No commit name provided in the LLM response. Skipping branch creation.")
            logger.debug("Processing patches")
            with console.status("[bold green]Processing patches...", spinner="dots") as status:
                run_dir_context = process_patches(run_dir_context, patch_processor)
            console.print("[bold green]Creating new files...")
            run_dir_context = perform_file_operations(run_dir_context, file_operator)
            with open(os.path.join(run_dir, "conversation_state.json"), 'w', encoding='utf-8') as f:
                json.dump(conversation_state.dict(), f, indent=2, cls=PydanticEncoder)
            console.print("[bold cyan]Running unit tests...[/bold cyan]")
            test_results = run_unit_tests()
            console.print(test_results)
            os.makedirs(run_dir, exist_ok=True)
            test_results_file = os.path.join(run_dir, f"test_results_turn_{conversation_state.turn_number}.txt")
            logger.info(f"Writing test results to: {test_results_file}")
            with open(test_results_file, 'w') as f:
                f.write(test_results)
            if "collected 0 items" not in test_results and "no tests ran" not in test_results:
                if not check_test_results(test_results):
                    append_test_results_to_next_prompt(run_dir, test_results, conversation_state.turn_number + 1)

            console.print("[bold cyan]Pipeline step completed. Waiting for user input...[/bold cyan]")
            if not get_user_approval("Do you want to continue the conversation?", InputType.CONTINUE_CONVERSATION):
                break

            resume = None

    except Exception as e:
        logger.error(f"An error occurred during pipeline execution: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        console.print(f"[bold red]Error: {str(e)}[/bold red]")
        return None

    console.print("[bold cyan]Running final unit tests...[/bold cyan]")
    final_test_results = run_unit_tests()
    console.print(final_test_results)
    console.print("[bold green]Pipeline execution completed.[/bold green]")
    logger.info(f"Pipeline execution completed. Results saved in {run_dir}")
    return run_dir_context

def main():
    # Load existing variables
    load_dotenv()

    # Check if current directory is a Git repository
    if not is_git_repo():
        console.print("[bold red]Error: Not a Git repository.[/bold red]")
        console.print("Please run 'git init' to initialize a Git repository before using My Engineer.")
        return

    # Check for ANTHROPIC_API_KEY
    anthropic_api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not anthropic_api_key:
        console.print("[yellow]ANTHROPIC_API_KEY not found in environment variables.[/yellow]")
        anthropic_api_key = input("Please enter your Anthropic API key: ").strip()
        
        # Save to .env file
        set_key(".env", "ANTHROPIC_API_KEY", anthropic_api_key)
        
        console.print("[green]API key saved to .env file.[/green]")
        
        # Reload environment variables
        load_dotenv()

    if args.auto_fix_tests:
        if not args.include_tests:
            console.print("[bold red]Error: --auto-fix-tests requires --include-tests[/bold blue]")
            sys.exit(1)
        auto_fix_tests(LLMPrompter(), InstructionProcessor(), PatchProcessor(), FileOperator(logger))
        sys.exit(0)
    get_config().set('use_cursor', args.use_cursor)

    if not args.prompt_file and not args.resume:
        console.print("[yellow]No prompt file provided. A temporary file will be opened in VSCode for you to enter your prompt.[/yellow]")

    try:
        run_dir_context = my_engineer_pipeline(args.prompt_file, args.include_tests, args.resume, args.use_cursor)
    except KeyboardInterrupt:
        logger.info("Process interrupted by user. Exiting gracefully...")
        print(f"\n{Fore.YELLOW}Process interrupted. Exiting gracefully...{Style.RESET_ALL}")
        console.print("[yellow]Process interrupted. Exiting gracefully...[/yellow]")
        sys.exit(0)
    except Exception as e:
        logger.error(f"An unhandled exception occurred: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        console.print(f"[bold red]Unhandled Error: {str(e)}[/bold red]")
        sys.exit(1)

if __name__ == "__main__":
    main()