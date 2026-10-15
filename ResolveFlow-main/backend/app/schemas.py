from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    email: str
    password: str


class UserRead(ORMModel):
    id: str
    email: str
    full_name: str
    role: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


class ConversationCreate(BaseModel):
    title: str = "新会话"


class ConversationRead(ORMModel):
    id: str
    title: str
    status: str
    created_at: datetime
    updated_at: datetime


class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=8000)


class MessageRead(ORMModel):
    id: str
    role: str
    content: str
    citations_json: str
    created_at: datetime


class Citation(BaseModel):
    title: str
    source: str
    score: float
    excerpt: str


class ToolTrace(BaseModel):
    tool: str
    status: str
    duration_ms: int = 0
    preview: str = ""


class AgentResponse(BaseModel):
    conversation_id: str
    message_id: str | None = None
    answer: str
    citations: list[Citation] = []
    traces: list[ToolTrace] = []
    pending_approval_id: str | None = None
    mode: str


class ApprovalDecision(BaseModel):
    decision: str = Field(pattern="^(approve|reject)$")
    note: str = ""


class ApprovalRead(ORMModel):
    id: str
    thread_id: str
    tool_name: str
    tool_args_json: str
    risk_level: str
    status: str
    reviewer_note: str
    created_at: datetime
    resolved_at: datetime | None


class TicketRead(ORMModel):
    id: str
    subject: str
    description: str
    priority: str
    status: str
    created_at: datetime


class OrderRead(ORMModel):
    id: str
    product_name: str
    amount: float
    status: str
    tracking_number: str | None
    refundable: bool


class KnowledgeCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    source: str = Field(default="manual", max_length=255)
    content: str = Field(min_length=20)


class KnowledgeRead(ORMModel):
    id: str
    title: str
    source: str
    status: str
    chunk_count: int
    created_at: datetime


class FeedbackCreate(BaseModel):
    message_id: str
    rating: int = Field(ge=-1, le=1)
    comment: str = Field(default="", max_length=1000)


class MetricsResponse(BaseModel):
    conversations: int
    open_tickets: int
    pending_approvals: int
    knowledge_documents: int
    tool_success_rate: float
    average_tool_latency_ms: float
    recent_tools: list[dict[str, Any]]

