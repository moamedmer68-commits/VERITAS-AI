from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from langchain_core.tools import tool
from sqlalchemy import select

from app.db.models import Order, Ticket
from app.db.session import SessionLocal
from app.services.rag import search_knowledge


@tool
def search_support_knowledge(query: str) -> str:
    """检索退款、物流、保修和人工升级等客服知识，回答政策问题时使用。"""
    return "由 ResolveFlow 运行时根据当前租户知识库执行。"


@tool
def get_order(order_id: str) -> str:
    """根据订单号查询订单商品、金额和当前状态。"""
    return "由 ResolveFlow 运行时执行订单查询。"


@tool
def track_shipment(order_id: str) -> str:
    """根据订单号查询物流单号和配送状态。"""
    return "由 ResolveFlow 运行时执行物流查询。"


@tool
def calculate_refund(order_id: str) -> str:
    """检查订单是否满足退款条件，不执行实际退款。"""
    return "由 ResolveFlow 运行时计算退款资格。"


@tool
def request_refund(order_id: str, reason: str) -> str:
    """提交退款申请。这是资金相关写操作，执行前必须由人工审批。"""
    return "由 ResolveFlow 运行时在审批通过后执行。"


@tool
def create_ticket(subject: str, description: str, priority: str = "medium") -> str:
    """创建客服工单，用于需要后续人工处理的问题。"""
    return "由 ResolveFlow 运行时创建工单。"


@tool
def handoff_to_human(reason: str) -> str:
    """将会话升级给人工客服，并创建高优先级工单。"""
    return "由 ResolveFlow 运行时执行人工转接。"


SUPPORT_TOOLS = [
    search_support_knowledge,
    get_order,
    track_shipment,
    calculate_refund,
    request_refund,
    create_ticket,
    handoff_to_human,
]

RISKY_TOOLS = {"request_refund"}


def execute_support_tool(
    tool_name: str,
    arguments: dict[str, Any],
    user_id: str,
    conversation_id: str,
) -> tuple[str, list[dict[str, Any]]]:
    with SessionLocal() as db:
        if tool_name == "search_support_knowledge":
            results = search_knowledge(db, str(arguments.get("query", "")))
            citations = [
                {
                    "title": item.title,
                    "source": item.source,
                    "score": round(item.score, 4),
                    "excerpt": item.content[:260],
                }
                for item in results
            ]
            payload = [
                {
                    "title": item.title,
                    "source": item.source,
                    "content": item.content,
                    "score": round(item.score, 4),
                }
                for item in results
            ]
            return json.dumps(payload, ensure_ascii=False), citations

        if tool_name in {"get_order", "track_shipment", "calculate_refund", "request_refund"}:
            order_id = str(arguments.get("order_id", ""))
            order = db.scalar(
                select(Order).where(Order.id == order_id, Order.user_id == user_id)
            )
            if order is None:
                return json.dumps({"error": "未找到该用户的订单"}, ensure_ascii=False), []

            if tool_name == "get_order":
                payload = _order_payload(order)
            elif tool_name == "track_shipment":
                payload = {
                    "order_id": order.id,
                    "status": order.status,
                    "tracking_number": order.tracking_number,
                    "latest_event": "运输途中，预计明日送达" if order.status == "shipped" else "订单已签收",
                }
            elif tool_name == "calculate_refund":
                payload = {
                    "order_id": order.id,
                    "eligible": order.refundable,
                    "amount": order.amount if order.refundable else 0,
                    "reason": "在可退款期限内" if order.refundable else "已超过无理由退货期限",
                }
            else:
                if not order.refundable:
                    return json.dumps({"error": "订单不满足退款条件"}, ensure_ascii=False), []
                order.status = "refund_requested"
                db.commit()
                payload = {
                    "order_id": order.id,
                    "status": order.status,
                    "amount": order.amount,
                    "reason": arguments.get("reason", "用户申请退款"),
                    "submitted_at": datetime.now(UTC).isoformat(),
                }
            return json.dumps(payload, ensure_ascii=False), []

        if tool_name in {"create_ticket", "handoff_to_human"}:
            if tool_name == "handoff_to_human":
                subject = "会话转人工"
                description = str(arguments.get("reason", "用户请求人工客服"))
                priority = "high"
            else:
                subject = str(arguments.get("subject", "客服问题"))
                description = str(arguments.get("description", ""))
                priority = str(arguments.get("priority", "medium"))
            ticket = Ticket(
                user_id=user_id,
                conversation_id=conversation_id,
                subject=subject,
                description=description,
                priority=priority if priority in {"low", "medium", "high"} else "medium",
            )
            db.add(ticket)
            db.commit()
            return json.dumps(
                {"ticket_id": ticket.id, "status": ticket.status, "priority": ticket.priority},
                ensure_ascii=False,
            ), []

        return json.dumps({"error": f"未知工具：{tool_name}"}, ensure_ascii=False), []


def _order_payload(order: Order) -> dict[str, Any]:
    return {
        "order_id": order.id,
        "product_name": order.product_name,
        "amount": order.amount,
        "status": order.status,
        "tracking_number": order.tracking_number,
        "refundable": order.refundable,
    }

