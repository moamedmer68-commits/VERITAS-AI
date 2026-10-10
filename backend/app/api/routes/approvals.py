from __future__ import annotations

import json
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.agent.graph import runtime
from app.api.deps import DbSession, StaffUser
from app.db.models import ApprovalRequest, Message
from app.schemas import AgentResponse, ApprovalDecision, ApprovalRead


router = APIRouter(prefix="/approvals", tags=["approvals"])


@router.get("", response_model=list[ApprovalRead])
def list_approvals(db: DbSession, _: StaffUser) -> list[ApprovalRequest]:
    return list(db.scalars(select(ApprovalRequest).order_by(ApprovalRequest.created_at.desc())))


@router.post("/{approval_id}/decision", response_model=AgentResponse)
def decide_approval(
    approval_id: str,
    payload: ApprovalDecision,
    db: DbSession,
    _: StaffUser,
) -> AgentResponse:
    approval = db.get(ApprovalRequest, approval_id)
    if approval is None:
        raise HTTPException(status_code=404, detail="审批不存在")
    if approval.status != "pending":
        raise HTTPException(status_code=409, detail="审批已处理")

    try:
        result = runtime.resume(approval.thread_id, payload.decision)
    except Exception as exc:
        raise HTTPException(status_code=409, detail="Agent 状态已失效，请重新发起请求") from exc

    approval.status = "approved" if payload.decision == "approve" else "rejected"
    approval.reviewer_note = payload.note
    approval.resolved_at = datetime.now(UTC)
    answer = result.get("answer", "审批处理完成")
    message = Message(
        conversation_id=approval.thread_id,
        role="assistant",
        content=answer,
        citations_json=json.dumps(result.get("citations", []), ensure_ascii=False),
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return AgentResponse(
        conversation_id=approval.thread_id,
        message_id=message.id,
        answer=answer,
        citations=result.get("citations", []),
        traces=result.get("traces", []),
        mode=result.get("mode", "offline"),
    )

