from __future__ import annotations

from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession, StaffUser
from app.db.models import (
    ApprovalRequest,
    Conversation,
    KnowledgeDocument,
    Order,
    Ticket,
    ToolExecution,
)
from app.schemas import MetricsResponse, OrderRead, TicketRead
from fastapi import APIRouter


router = APIRouter(tags=["operations"])


@router.get("/orders", response_model=list[OrderRead])
def list_orders(db: DbSession, user: CurrentUser) -> list[Order]:
    return list(db.scalars(select(Order).where(Order.user_id == user.id)))


@router.get("/tickets", response_model=list[TicketRead])
def list_tickets(db: DbSession, user: CurrentUser) -> list[Ticket]:
    query = select(Ticket).order_by(Ticket.created_at.desc())
    if user.role == "customer":
        query = query.where(Ticket.user_id == user.id)
    return list(db.scalars(query))


@router.get("/metrics", response_model=MetricsResponse)
def metrics(db: DbSession, _: StaffUser) -> MetricsResponse:
    conversations = db.scalar(select(func.count()).select_from(Conversation)) or 0
    open_tickets = db.scalar(
        select(func.count()).select_from(Ticket).where(Ticket.status == "open")
    ) or 0
    pending = db.scalar(
        select(func.count()).select_from(ApprovalRequest).where(ApprovalRequest.status == "pending")
    ) or 0
    documents = db.scalar(select(func.count()).select_from(KnowledgeDocument)) or 0
    total_tools = db.scalar(select(func.count()).select_from(ToolExecution)) or 0
    successful_tools = db.scalar(
        select(func.count()).select_from(ToolExecution).where(ToolExecution.status == "completed")
    ) or 0
    average_latency = db.scalar(select(func.avg(ToolExecution.duration_ms))) or 0
    recent = list(db.scalars(select(ToolExecution).order_by(ToolExecution.created_at.desc()).limit(8)))
    return MetricsResponse(
        conversations=conversations,
        open_tickets=open_tickets,
        pending_approvals=pending,
        knowledge_documents=documents,
        tool_success_rate=round(successful_tools / total_tools * 100, 1) if total_tools else 100.0,
        average_tool_latency_ms=round(float(average_latency), 1),
        recent_tools=[
            {
                "tool": item.tool_name,
                "status": item.status,
                "duration_ms": item.duration_ms,
                "created_at": item.created_at.isoformat(),
            }
            for item in recent
        ],
    )

