from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

MessageRole = Literal["user", "assistant", "system"]

ChatContextKind = Literal["sentence", "quiz", "quiz_attempt", "lecture"]
ChatContextReason = Literal[
    "explain_mistake",
    "explain_item",
    "grammar_help",
    "vocabulary_help",
    "custom",
]


class ChatContext(BaseModel):
    kind: ChatContextKind
    sentence_id: str | None = None
    quiz_id: str | None = None
    attempt_id: str | None = None
    lecture_id: str | None = None
    reason: ChatContextReason | None = None

    @model_validator(mode="after")
    def _require_id_for_kind(self) -> "ChatContext":
        mapping = {
            "sentence": self.sentence_id,
            "quiz": self.quiz_id,
            "quiz_attempt": self.attempt_id,
            "lecture": self.lecture_id,
        }
        if mapping[self.kind] is None:
            raise ValueError(f"context.kind={self.kind!r} requires the matching *_id field")
        return self


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
    context: ChatContext | None = Field(
        default=None,
        description="If present, the conversation is anchored to a specific study item.",
    )


class ConversationsResponse(BaseModel):
    items: list[ChatConversation]


class StartConversationRequest(BaseModel):
    topic: str | None = None
    initial_message: str | None = Field(
        default=None,
        description="Optional first user message. If omitted and auto_assistant_reply=false, the conversation starts empty.",
    )
    context: ChatContext | None = Field(
        default=None,
        description=(
            "Structured context so the AI already knows what the user is looking at "
            "(sentence, quiz, lecture, or a past attempt). Set when the chatbot icon is opened "
            "from a study screen."
        ),
    )
    auto_assistant_reply: bool = Field(
        default=False,
        description=(
            "When true, the server generates the first assistant message from `context` alone, "
            "without requiring any user input. Powers CTAs like 'Would you like an explanation?'."
        ),
    )


class StartConversationResponse(BaseModel):
    conversation: ChatConversation
    first_assistant_message: ChatMessage | None = Field(
        default=None,
        description="Populated when auto_assistant_reply was requested and the server produced a reply.",
    )


class MessagesResponse(BaseModel):
    items: list[ChatMessage]
    next_cursor: str | None = None


class SendMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=2000)


class SendMessageResponse(BaseModel):
    user_message: ChatMessage
    assistant_message: ChatMessage
