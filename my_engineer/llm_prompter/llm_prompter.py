from my_engineer.llm_prompter.src.chat_engine import ChatEngine
from my_engineer.shared_models.chat_models import ConversationState
from my_engineer.shared_utils.logger import setup_logger

class LLMPrompter:
    def __init__(self, provider_name: str = "claude", run_dir: str = None):
        assert run_dir, "run_dir must be provided when initializing LLMPrompter"
        self.logger = setup_logger("LLMPrompter")
        self._chat_engine = ChatEngine(provider_name, run_dir)

    def generate_instructions(self, conversation_state: ConversationState, user_prompt: str) -> str:
        """
        Generate instructions based on the given conversation state.
        Args:
            conversation_state (ConversationState): The current state of the conversation.
            user_prompt (str): The user's prompt or request.
        Returns:
            str: Generated instructions.
        """
        self.logger.debug("Generating instructions in LLMPrompter")
        self.logger.debug(f"User prompt: {user_prompt[:100]}...")  # Log first 100 chars of user prompt
        return self._chat_engine.get_raw_instructions(conversation_state, user_prompt)