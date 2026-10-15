from __future__ import annotations

import json
from collections.abc import AsyncIterable
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException
from fastapi.sse import EventSourceResponse, ServerSentEvent
from sqlalchemy import select

from app.agent.graph import runtime
from app.api.deps import CurrentUser, DbSession
from app.db.models import ApprovalRequest, Conversation, Feedback, Message
from app.schemas import (
    AgentResponse,
    ConversationCreate,
    ConversationRead,
    FeedbackCreate,
    MessageCreate,
    MessageRead,
)


router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", response_model=list[ConversationRead])
def list_conversations(db: DbSession, user: CurrentUser) -> list[Conversation]:
    return list(
        db.scalars(
            select(Conversation)
            .where(Conversation.user_id == user.id)
            .order_by(Conversation.updated_at.desc())
        )
    )


@router.post("", response_model=ConversationRead)
def create_conversation(
    payload: ConversationCreate,
    db: DbSession,
    user: CurrentUser,
) -> Conversation:
    conversation = Conversation(user_id=user.id, title=payload.title)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


@router.get("/{conversation_id}/messages", response_model=list[MessageRead])
def list_messages(
    conversation_id: str,
    db: DbSession,
    user: CurrentUser,
) -> list[Message]:
    _owned_conversation(db, conversation_id, user.id)
    return list(
        db.scalars(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
        )
    )


@router.post("/{conversation_id}/messages", response_model=AgentResponse)
def send_message(
    conversation_id: str,
    payload: MessageCreate,
    db: DbSession,
    user: CurrentUser,
) -> AgentResponse:
    conversation = _owned_conversation(db, conversation_id, user.id)
    return _process_message(db, conversation, user.id, payload.content)


@router.post("/{conversation_id}/messages/stream", response_class=EventSourceResponse)
async def stream_message(
    conversation_id: str,
    payload: MessageCreate,
    db: DbSession,
    user: CurrentUser,
) -> AsyncIterable[ServerSentEvent]:
    conversation = _owned_conversation(db, conversation_id, user.id)
    result = _process_message(db, conversation, user.id, payload.content)
    yield ServerSentEvent(data={"stage": "planning"}, event="status")
    for trace in result.traces:
        yield ServerSentEvent(data=trace.model_dump(), event="tool")
    yield ServerSentEvent(data=result.model_dump(), event="message")
    yield ServerSentEvent(raw_data="[DONE]", event="done")


@router.post("/feedback", status_code=201)
def create_feedback(payload: FeedbackCreate, db: DbSession, user: CurrentUser) -> dict[str, str]:
    message = db.get(Message, payload.message_id)
    if message is None:
        raise HTTPException(status_code=404, detail="消息不存在")
    conversation = _owned_conversation(db, message.conversation_id, user.id)
    feedback = Feedback(
        message_id=message.id,
        user_id=conversation.user_id,
        rating=payload.rating,
        comment=payload.comment,
    )
    db.add(feedback)
    db.commit()
    return {"id": feedback.id}


def _process_message(
    db: DbSession,
    conversation: Conversation,
    user_id: str,
    content: str,
) -> AgentResponse:
    user_message = Message(conversation_id=conversation.id, role="user", content=content)
    db.add(user_message)
    if conversation.title == "新会话":
        conversation.title = content[:30]
    conversation.updated_at = datetime.now(UTC)
    db.commit()

    result = runtime.invoke(conversation.id, user_id, conversation.id, content)
    pending_approval_id: str | None = None
    answer = result.get("answer", "")

    if interrupts := result.get("__interrupt__"):
        request = interrupts[0].value
        approval = ApprovalRequest(
            thread_id=conversation.id,
            user_id=user_id,
            tool_name=request["tool_name"],
            tool_args_json=json.dumps(request["arguments"], ensure_ascii=False),
            risk_level=request.get("risk_level", "high"),
        )
        db.add(approval)
        db.commit()
        db.refresh(approval)
        pending_approval_id = approval.id
        answer = "退款申请已完成资格判断，正在等待人工客服审批；审批前不会修改订单状态。"

    citations = result.get("citations", [])
    assistant_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=answer,
        citations_json=json.dumps(citations, ensure_ascii=False),
    )
    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)
    return AgentResponse(
        conversation_id=conversation.id,
        message_id=assistant_message.id,
        answer=answer,
        citations=citations,
        traces=result.get("traces", []),
        pending_approval_id=pending_approval_id,
        mode=result.get("mode", "offline"),
    )


def _owned_conversation(db: DbSession, conversation_id: str, user_id: str) -> Conversation:
    conversation = db.scalar(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id,
        )
    )
    if conversation is None:
        raise HTTPException(status_code=404, detail="会话不存在")
    return conversation
