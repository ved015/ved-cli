from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

@dataclass
class TextDelta:
    content : str

    def __str__(self):
        return self.content

class StreamEventType(str, Enum):
    TEXT_DELTA = "text_delta"
    MESSAGE_COMPLETE = "message_complete"
    ERROR = "error"

@dataclass
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens : int = 0
    total_tokens : int = 0
    cached_tokens : int = 0

    def __add__(self, second : TokenUsage):
        return TokenUsage(
            prompt_tokens = self.prompt_tokens + second.prompt_tokens,
            completion_tokens = self.completion_tokens + second.completion_tokens,
            total_tokens = self.total_tokens + second.total_tokens,
            cached_tokens = self.cached_tokens + second.cached_tokens,
        )

@dataclass
class StreamEvent:
    type : StreamEventType
    text_delta : TextDelta | None = None
    error : str | None = None
    finish_reason : str | None = None
    usage : TokenUsage | None = None