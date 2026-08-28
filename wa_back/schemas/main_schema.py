from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Optional
from dependencies.settings import get_settings

settings = get_settings()

class Query(BaseModel):
    prompt: str = "Merhaba"
    model: str = settings.model
    stream: bool = False
    think: bool = False

class Conversation(BaseModel):
    id: str
    messages: List[Dict[str, str]] = []


class WhatsAppMessage(BaseModel):
    id: str
    from_: str
    fromMe: bool
    type: str
    text: Optional[str] = None
    filePath: Optional[str] = None
    timestamp: Optional[int] = None
