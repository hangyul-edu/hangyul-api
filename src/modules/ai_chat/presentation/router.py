from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, status

from src.common.security.auth import CurrentUser, get_current_user
from src.modules.ai_chat.presentation.schemas import (
    ChatContext,
    ChatConversation,
    ChatMessage,
    ConversationsResponse,
    MessagesResponse,
    SendMessageRequest,
    SendMessageResponse,
    StartConversationRequest,
    StartConversationResponse,
)

router = APIRouter(prefix="/ai/conversations", tags=["ai-chat"])


def _auto_reply_for(context: ChatContext | None) -> ChatMessage:
    """Stub — real service would run the LLM with context in the system prompt."""
    now = datetime.now(timezone.utc)
    if context is None:
        content = "무엇을 도와드릴까요?"
    elif context.kind == "quiz_attempt" and context.reason == "explain_mistake":
        content = (
            "이번에 고른 답은 제시된 문맥과 잘 맞지 않아요. 정답과의 차이를 단계별로 설명드릴게요."
        )
    elif context.kind == "sentence":
        content = "이 문장의 뜻과 사용 상황을 쉽게 풀어드릴게요. 어떤 부분이 가장 궁금하신가요?"
    elif context.kind == "quiz":
        content = "문제를 풀기 전에 도움이 필요하신가요? 핵심 문법 포인트부터 짚어드릴게요."
    elif context.kind == "lecture":
        content = "강의 내용 중 어떤 부분을 다시 짚어드릴까요?"
    else:
        content = "어떤 도움이 필요하신가요?"
    return ChatMessage(
        message_id=f"msg_{uuid4().hex[:12]}",
        role="assistant",
        content=content,
        created_at=now,
        suggestion_chips=[],
    )


@router.post(
    "",
    response_model=StartConversationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new HangulAI conversation (supports context + auto assistant reply)",
)
def start_conversation(
    payload: StartConversationRequest, user: CurrentUser = Depends(get_current_user)
) -> StartConversationResponse:
    now = datetime.now(timezone.utc)
    conversation = ChatConversation(
        conversation_id=f"cnv_{uuid4().hex[:12]}",
        title=payload.topic or "한글AI와 대화",
        last_message_at=now,
        unread_count=0,
        context=payload.context,
    )
    first = _auto_reply_for(payload.context) if payload.auto_assistant_reply else None
    return StartConversationResponse(conversation=conversation, first_assistant_message=first)


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
