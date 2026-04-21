from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

MessageRole = Literal["user", "assistant", "system"]


class ChatMessage(BaseModel):
    message_id: str
    role: MessageRole
    content: str
    created_at: datetime
    suggestion_chips: list[str] = Field(default_factory=list)


class ChatConversation(BaseModel):
    conversation_id: str
    title: str
    last_message_at: datetime | None = None
    unread_count: int = 0


class ConversationsResponse(BaseModel):
    items: list[ChatConversation]


class StartConversationRequest(BaseModel):
    topic: str | None = None
    initial_message: str | None = None


class MessagesResponse(BaseModel):
    items: list[ChatMessage]
    next_cursor: str | None = None


class SendMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=2000)


class SendMessageResponse(BaseModel):
    user_message: ChatMessage
    assistant_message: ChatMessage
