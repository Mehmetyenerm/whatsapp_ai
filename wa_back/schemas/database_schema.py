from sqlmodel import SQLModel, Field
from uuid import uuid4, UUID
from enum import Enum

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class Conversation(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    phone: int = Field(index=True, unique=True)

class Message(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    conversation_id: UUID = Field(foreign_key="conversation.id")
    role: MessageRole          # user / assistant
    content: str
    created_at: int