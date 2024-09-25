from colorama import Fore, init
import threading
import time
import select
import sys
import os
from ..shared_utils.logger import setup_logger, get_log_file_path
from enum import Enum, auto

TOTAL_SECONDS = 300

logger = setup_logger("user_input")

# Initialize colorama
init(autoreset=True)

class InputType(Enum):
    CONTINUE_CONVERSATION = auto()
    GENERAL = auto()

def display_countdown(stop_event):
    remaining_seconds = TOTAL_SECONDS
    while remaining_seconds > 0 and not stop_event.is_set():
        minutes, seconds = divmod(remaining_seconds, 60)
        if remaining_seconds % 30 == 0:
            print(f"\n{Fore.YELLOW}Time remaining: {minutes:02d}:{seconds:02d}{Fore.RESET}")
        time.sleep(1)
        remaining_seconds -= 1
    
    if not stop_event.is_set():
        print(f"\n{Fore.YELLOW}Warning: Time's up! Do you want to continue? (Y/n){Fore.RESET}")

def start_timer(input_type):
    stop_event = threading.Event()
    timer_thread = threading.Thread(target=display_countdown, args=(stop_event,))
    timer_thread.start()
    return stop_event, timer_thread

def stop_timer(stop_event, timer_thread):
    stop_event.set()
    timer_thread.join()

def get_input_with_timeout(prompt, input_type=InputType.GENERAL):
    stop_event = None
    timer_thread = None
    if input_type == InputType.CONTINUE_CONVERSATION:
        stop_event, timer_thread = start_timer(input_type)
    
    user_input = None
    while user_input is None:
        if input_available() or input_type == InputType.GENERAL:
            user_input = input()
        time.sleep(0.1)
    if stop_event and timer_thread:
        stop_timer(stop_event, timer_thread)
    return user_input

def input_available():
    return select.select([sys.stdin], [], [], 0.0)[0]

def get_user_approval(prompt: str, input_type: InputType = InputType.GENERAL) -> bool:
    if 'PYTEST_CURRENT_TEST' in os.environ:
        return get_user_approval.mock_response
    else:
        stop_event = None
        timer_thread = None
        if input_type == InputType.CONTINUE_CONVERSATION:
            stop_event, timer_thread = start_timer(input_type)
        
        logger.info(f"{prompt} (Y/n)")
        response = input().lower().strip()
        
        if stop_event and timer_thread:
            stop_timer(stop_event, timer_thread)
        
        return response in ['y', 'yes', '']

get_user_approval.mock_response = True