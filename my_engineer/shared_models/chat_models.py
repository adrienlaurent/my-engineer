from pydantic import BaseModel, Field, field_validator
from typing import List, Literal, Optional, Union, Dict

class MessageContent(BaseModel):
    type: Literal["text"] = "text"
    text: str

class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: Union[str, List[MessageContent]]

    @classmethod
    def from_dict(cls, data: Dict):
        v = data.get('content')
        if isinstance(v, dict):
            data['content'] = MessageContent(**v)
        return cls(**data)

class MessageSequence(BaseModel):
    messages: List[Message] = Field(default_factory=list)

    @field_validator("messages")
    def validate_message_sequence(cls, messages):
        if len(messages) > 1:
            for i in range(1, len(messages)):
                if messages[i-1].role == "user" and messages[i].role != "assistant":
                    raise ValueError("An assistant message must follow each user message")
                if messages[i-1].role == "assistant" and messages[i].role != "user":
                    raise ValueError("A user message must follow each assistant message")
        return messages

class ConversationState(BaseModel):
    turn_number: int = Field(default=1, ge=1)
    message_sequence: MessageSequence = Field(default_factory=MessageSequence)
    previous_run: Optional[str] = None
    context: Optional[str] = None
    smart_context_added: bool = False

    @classmethod
    def from_dict(cls, data: Dict):
        if 'message_sequence' in data and 'messages' in data['message_sequence']:
            data['message_sequence']['messages'] = [Message.from_dict(m) for m in data['message_sequence']['messages']]
        return cls(**data)