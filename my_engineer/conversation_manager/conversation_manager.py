import json
import os
from typing import Optional
from pydantic import BaseModel
from ..shared_utils.logger import setup_logger
from ..shared_utils.error_handler import ErrorHandler
from ..shared_models.chat_models import ConversationState

logger = setup_logger("conversation_manager")
error_handler = ErrorHandler(logger)

class PydanticEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, BaseModel):
            return obj.dict()
        return super().default(obj)

class ConversationManager:
    @staticmethod
    def save_state(run_dir: str, state: ConversationState) -> None:
        try:
            state_file = os.path.join(run_dir, "conversation_state.json")
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(state.dict(), f, indent=2, cls=PydanticEncoder)
            logger.info(f"Conversation state saved to {state_file}")
        except Exception as e:
            error_handler.handle_exception(e, "saving conversation state")

    @staticmethod
    def load_state(run_dir: str) -> Optional[ConversationState]:
        try:
            state_file = os.path.join(run_dir, "conversation_state.json")
            if os.path.exists(state_file):
                with open(state_file, 'r') as f:
                    state_dict = json.load(f)
                return ConversationState.from_dict(state_dict)
            logger.info(f"No existing conversation state found in {run_dir}")
            return None
        except Exception as e:
            error_handler.handle_exception(e, "loading conversation state")
            return None

    @staticmethod
    def update_state(run_dir: str, new_data: dict) -> None:
        """
        Update the conversation state with new data.

        Args:
            run_dir (str): The directory where the state file is located.
            new_data (dict): The new data to update the state with.

        Raises:
            Exception: If there's an error updating the state.
        """
        try:
            current_state = ConversationManager.load_state(run_dir) or ConversationState()
            updated_state = ConversationState(**{**current_state.dict(), **new_data})
            ConversationManager.save_state(run_dir, updated_state)
            logger.info(f"Conversation state updated in {run_dir}")
        except Exception as e:
            error_handler.handle_exception(e, "updating conversation state")