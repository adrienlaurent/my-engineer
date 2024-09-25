import argparse
from ..shared_models.chat_models import ConversationState
from .src.chat_engine import ChatEngine
from ..shared_utils.logger import setup_logger
from dotenv import load_dotenv
import os

logger = setup_logger(__name__)
load_dotenv(dotenv_path=os.path.join(os.getcwd(), ".env"))
  # Load environment variables from .env file

def main(test_mode=False):
    parser = argparse.ArgumentParser(description="LLM Prompter")
    parser.add_argument("--provider", choices=["claude", "chatgpt"], default="claude", help="Choose the LLM provider")
    parser.add_argument("input", help="Path to the prompt file")
    args = parser.parse_args()

    try:
        with open(args.input, 'r') as file:
            prompt_content = file.read().strip()
        logger.info("Generating instructions")
        chat_engine = ChatEngine(provider_name=args.provider, logger=logger)
        conversation_state = ConversationState()
        raw_instructions = chat_engine.get_raw_instructions(conversation_state, prompt_content)
        print(raw_instructions)
    except FileNotFoundError:
        logger.error(f"Prompt file not found: {args.input}")
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()