from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, status

from src.common.security.auth import CurrentUser, get_current_user
from src.modules.ai_chat.presentation.schemas import (
    ChatConversation,
    ChatMessage,
    ConversationsResponse,
    MessagesResponse,
    SendMessageRequest,
    SendMessageResponse,
    StartConversationRequest,
)

router = APIRouter(prefix="/ai/conversations", tags=["ai-chat"])


@router.post(
    "",
    response_model=ChatConversation,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new HangulAI conversation",
)
def start_conversation(
    payload: StartConversationRequest, user: CurrentUser = Depends(get_current_user)
) -> ChatConversation:
    return ChatConversation(
        conversation_id=f"cnv_{uuid4().hex[:12]}",
        title=payload.topic or "한글AI와 대화",
        last_message_at=datetime.now(timezone.utc),
        unread_count=0,
    )


@router.get("", response_model=ConversationsResponse, summary="List conversations")
def list_conversations(user: CurrentUser = Depends(get_current_user)) -> ConversationsResponse:
    return ConversationsResponse(items=[])


@router.get("/{conversation_id}/messages", response_model=MessagesResponse, summary="List messages in a conversation")
def list_messages(
    conversation_id: str,
    cursor: str | None = None,
    user: CurrentUser = Depends(get_current_user),
) -> MessagesResponse:
    return MessagesResponse(items=[])


@router.post(
    "/{conversation_id}/messages",
    response_model=SendMessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send a message and receive an AI reply",
)
def send_message(
    conversation_id: str,
    payload: SendMessageRequest,
    user: CurrentUser = Depends(get_current_user),
) -> SendMessageResponse:
    now = datetime.now(timezone.utc)
    return SendMessageResponse(
        user_message=ChatMessage(
            message_id=f"msg_{uuid4().hex[:12]}",
            role="user",
            content=payload.content,
            created_at=now,
        ),
        assistant_message=ChatMessage(
            message_id=f"msg_{uuid4().hex[:12]}",
            role="assistant",
            content="좋은 질문이에요! 친구에게는 이렇게 말해봐요: \"요즘 어떻게 지내?\"",
            created_at=now,
            suggestion_chips=["더 자연스럽게", "존댓말로 바꿔줘"],
        ),
    )
