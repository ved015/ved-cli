from prompts.system import get_system_prompt
from dataclasses import dataclass
from typing import Optional,Any
from dotenv import load_dotenv
import os

load_dotenv()
model = os.getenv('MODEL')

from utils.text import count_token

@dataclass
class messageItem:
    role : str
    content : str
    token_count : Optional[int] = None

    def to_dict(self) -> dict[str, Any]:
        result : dict[str, Any] = {
            "role" : self.role
        }

        if self.content:
            result["content"] = self.content
        
        return result

class ContextManager:
    def __init__(self) -> None:
        self._system_prompt = get_system_prompt()
        self._messages : list[messageItem] = []     
        self._model = model 

    def add_user_message(self, content : str) -> None:
        item = messageItem(
            role = 'user',
            content = content,
            token_count = count_token(content , self._model),
        )

        self._messages.append(item)
    
    def add_assistant_message(self, content : str) -> None:
        item = messageItem(
            role = 'assistant',
            content = content or "",
            token_count = count_token(content , self._model),
        )

        self._messages.append(item)
    
    def get_messages(self) -> list[dict[str, Any]]:
        messages = []

        if self._system_prompt:
            messages.append(
                {
                    "role" : "system",
                    "content" : self._system_prompt,
                }
            )
        
        for item in self._messages:
            messages.append(item.to_dict())
        
        return messages