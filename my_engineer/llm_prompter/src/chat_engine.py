import json
from typing import List, Dict, Optional
from ...llm_providers import get_provider
from ...llm_providers import Settings
from ...llm_providers.providers.exceptions import OverloadedError
from ...llm_providers.providers.utils import log_llm_request
from .context_utils import get_context
from ...shared_models.chat_models import Message, ConversationState, MessageContent
from ...shared_utils.logger import setup_logger
from colorama import Fore, init
from rich.console import Console
from rich.spinner import Spinner
init(autoreset=True)

class ChatEngine:
    def __init__(self, provider_name: str, run_dir: str = None):
        self.llm_provider = get_provider(provider_name, run_dir)
        self.logger = setup_logger(__name__)
        self.settings = Settings()
        self.console = Console()
        self.run_dir = run_dir

    def get_raw_instructions(self, conversation_state: ConversationState, user_prompt: str) -> str:
        try:
            assert self.run_dir, "run_dir must be provided when initializing ChatEngine"
            if not conversation_state.message_sequence.messages:
                self.initialize_conversation_state(conversation_state, False, user_prompt)
            messages = self.prepare_messages(conversation_state, user_prompt)
            self.logger.debug(f"Prepared messages: {json.dumps(messages, indent=2)}")

            log_llm_request(self.llm_provider.model)
            with self.console.status("[bold green]Sending request to LLM...", spinner="dots") as status:
                response = self.llm_provider.generate_response(messages)
                status.update("[bold green]Request completed!")
                self.console.print("[bold green]Response received from LLM.")

            if not isinstance(response, str) or not response.strip():
                raise ValueError("Received an empty or invalid response from the LLM provider")

            conversation_state.message_sequence.messages.append(Message(role="user", content=user_prompt))
            conversation_state.message_sequence.messages.append(Message(role="assistant", content=response))

            return response
        except OverloadedError as e:
            self.logger.error(f"LLM provider is overloaded: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Error getting raw instructions: {str(e)}")
            raise

    def initialize_conversation_state(self, conversation_state: ConversationState, include_tests: bool = False, user_request: str = "") -> None:
        assert self.run_dir, "run_dir must be provided when initializing ChatEngine"
        assert user_request != "", "user_request must exist"
        run_dir = self.run_dir
        context = get_context(include_tests=include_tests, user_request=user_request, run_dir=run_dir)
        self.logger.info(f"Initializing conversation state with run_dir: {run_dir}")
        context_message = Message(
            role="user",
            content=[
                MessageContent(
                    type="text",
                    text=f"<context>{context}</context>",
                ),
            ]
        )
        assistant_message = Message(
            role="assistant",
            content=[
                MessageContent(
                    type="text",
                    text="Thank you for providing this initial context. How can I help?",
                ),
            ]
        )
        conversation_state.message_sequence.messages.append(context_message)
        conversation_state.message_sequence.messages.append(assistant_message)
        self.logger.info(Fore.BLUE + f"Initialized conversation state with cached context.")

    def prepare_messages(self, conversation_state: ConversationState, user_prompt: str) -> List[Dict[str, str]]:
        messages = []
        for msg in conversation_state.message_sequence.messages:
            if isinstance(msg.content, list):
                content = " ".join(item.text for item in msg.content if item.type == "text")
            else:
                content = msg.content
            messages.append({"role": msg.role, "content": content})
        messages.append({"role": "user", "content": user_prompt})
        return messages

    def set_run_dir(self, run_dir: str):
        self.run_dir = run_dir