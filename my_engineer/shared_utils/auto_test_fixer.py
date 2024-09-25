import subprocess
import os
import re
from typing import Optional
from ..shared_utils.logger import setup_logger
from ..shared_utils.test_runner.test_runner import run_unit_tests, check_test_results, get_first_failed_test
from ..shared_models.chat_models import ConversationState
from ..shared_utils.pipeline_helpers import setup_run_directory
from ..shared_utils.user_input import get_user_approval
from ..conversation_manager import ConversationManager
from colorama import Fore, init

logger = setup_logger("auto_test_fixer")
init(autoreset=True)  # Initialize colorama

def fix_tests(llm_prompter, instruction_processor, patch_processor, file_operator, pytest_output: str, run_dir: str) -> bool:
    conversation_state = ConversationManager.load_state(run_dir) or ConversationState()
    first_failed_test = get_first_failed_test(pytest_output)
    if first_failed_test is None:
        logger.info("No specific failed test found in pytest output. Attempting to fix general errors.")
        first_failed_test = "general error"
    
    prompt = (
        f"Focus on fixing only the first failed test: {first_failed_test}. "
        f"The codebase context is already included by default. "
        f"Do not attempt to fix any other tests at this time. "
        f"Analyze the following pytest output and suggest a fix:\n\n{pytest_output}\n"
        f"Provide your fix in the form of a patch that can be applied to the relevant file. "
        f"If the error is related to missing dependencies, suggest the correct pip install command."
    )
    
    raw_instructions = llm_prompter.generate_instructions(conversation_state, prompt)
    llm_response = instruction_processor.process(raw_instructions)
    
    # Save the conversation state
    ConversationManager.save_state(run_dir, conversation_state)
    
    if llm_response.patches:
        for patch in llm_response.patches:
            patch_processor.process_patches([patch], ".")  # Use current directory
        logger.info(f"Applied fix to test: {first_failed_test}")
        return True
    else:
        logger.info(f"No fix could be determined for test: {first_failed_test}")
        return False

def auto_fix_tests(
    llm_prompter,
    instruction_processor,
    patch_processor,
    file_operator,
    max_attempts: int = 3
):
    run_dir = setup_run_directory()
    logger.info(f"Created run directory for auto-fix: {run_dir}")
    logger.info(f"Current working directory: {os.getcwd()}")
    
    # Initialize conversation state
    initial_state = ConversationState()
    ConversationManager.save_state(run_dir, initial_state)
    
    pytest_output = run_unit_tests()
    print(f"\n{Fore.CYAN}Initial Test Results:{Fore.RESET}")
    print(pytest_output)

    if isinstance(pytest_output, str) and pytest_output.startswith("Error running pytest:"):
        print(f"\n{Fore.RED}{pytest_output}{Fore.RESET}")
        logger.error("Error running pytest. Exiting auto-fix process.")
        return

    if check_test_results(pytest_output):
        print(f"\n{Fore.GREEN}All tests passed!{Fore.RESET}")
        logger.info("All tests passed!")
        return

    logger.info("Tests failed. Starting auto-fix process.")
    
    first_failed_test = get_first_failed_test(pytest_output)
    if first_failed_test:
        print(f"\n{Fore.YELLOW}First failed test or error: {first_failed_test}{Fore.RESET}")
    else:
        print(f"\n{Fore.YELLOW}No specific test failure identified. There might be a general error.{Fore.RESET}")
    
    for attempt in range(1, max_attempts + 1):
        logger.info(f"Auto-fix attempt {attempt}")
        
        fixes_applied = fix_tests(
            llm_prompter, instruction_processor, patch_processor,
            file_operator, pytest_output, run_dir
        )
        
        if fixes_applied:
            pytest_output = run_unit_tests()
            print(f"\n{Fore.CYAN}Test Results after fix attempt {attempt}:{Fore.RESET}")
            print(pytest_output)
            
            if check_test_results(pytest_output):
                print(f"\n{Fore.GREEN}All tests passed after auto-fix attempts!{Fore.RESET}")
                logger.info("All tests passed after auto-fix")
                break
        else:
            logger.info(f"No fixes could be applied in attempt {attempt}")
        
        if attempt < max_attempts:
            retry = get_user_approval(f"\nAttempt {attempt} completed. Do you want to try another auto-fix pass?")
            if not retry:
                print(f"{Fore.YELLOW}Auto-fix process ended by user.{Fore.RESET}")
                break
        else:
            print(f"{Fore.YELLOW}Reached maximum number of auto-fix attempts.{Fore.RESET}")

    # Display final results
    print(f"\n{Fore.CYAN}=== Final Test Results ==={Fore.RESET}")
    logger.info("Completed auto-fix attempts.")