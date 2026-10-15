from __future__ import annotations

import json
import re
import time
from typing import Any, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_deepseek import ChatDeepSeek
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from app.agent.tools import RISKY_TOOLS, SUPPORT_TOOLS, execute_support_tool
from app.core.config import get_settings
from app.db.models import ToolExecution
from app.db.session import SessionLocal


SYSTEM_PROMPT = """你是 ResolveFlow 企业客服 Agent。你必须基于知识库或业务工具结果回答，
不能编造订单、物流、政策或处理结果。涉及退款时使用 request_refund；该工具会由系统要求人工审批。
用户明确要求人工、涉及账户安全或法律投诉时使用 handoff_to_human。
每次最多选择一个最必要的工具。工具参数必须来自用户消息，不确定订单号时先询问。"""


class SupportState(TypedDict, total=False):
    user_id: str
    conversation_id: str
    user_message: str
    tool_call: dict[str, Any]
    tool_result: str
    citations: list[dict[str, Any]]
    traces: list[dict[str, Any]]
    approval_status: str
    answer: str
    mode: str


class SupportAgentRuntime:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.checkpointer = InMemorySaver()
        self.graph = self._build_graph()

    def invoke(
        self,
        thread_id: str,
        user_id: str,
        conversation_id: str,
        message: str,
    ) -> dict[str, Any]:
        config = {"configurable": {"thread_id": thread_id}}
        return self.graph.invoke(
            {
                "user_id": user_id,
                "conversation_id": conversation_id,
                "user_message": message,
                "traces": [],
                "citations": [],
                "mode": "llm" if self.settings.has_llm else "offline",
            },
            config=config,
        )

    def resume(self, thread_id: str, decision: str) -> dict[str, Any]:
        config = {"configurable": {"thread_id": thread_id}}
        return self.graph.invoke(Command(resume={"decision": decision}), config=config)

    def _build_graph(self):
        builder = StateGraph(SupportState)
        builder.add_node("plan", self._plan)
        builder.add_node("approval", self._approval)
        builder.add_node("execute", self._execute)
        builder.add_node("compose", self._compose)
        builder.add_edge(START, "plan")
        builder.add_conditional_edges(
            "plan",
            lambda state: "approval" if state["tool_call"]["name"] in RISKY_TOOLS else "execute",
            {"approval": "approval", "execute": "execute"},
        )
        builder.add_conditional_edges(
            "approval",
            lambda state: "execute" if state.get("approval_status") == "approve" else "compose",
            {"execute": "execute", "compose": "compose"},
        )
        builder.add_edge("execute", "compose")
        builder.add_edge("compose", END)
        return builder.compile(checkpointer=self.checkpointer)

    def _plan(self, state: SupportState) -> dict[str, Any]:
        if self.settings.has_llm:
            try:
                model = ChatDeepSeek(
                    model=self.settings.deepseek_model,
                    api_key=self.settings.deepseek_api_key,
                    base_url=self.settings.deepseek_base_url,
                    temperature=0,
                ).bind_tools(SUPPORT_TOOLS)
                response = model.invoke(
                    [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=state["user_message"])]
                )
                if response.tool_calls:
                    call = response.tool_calls[0]
                    return {"tool_call": {"name": call["name"], "args": call["args"]}}
            except Exception:
                pass
        return {"tool_call": _offline_plan(state["user_message"])}

    def _approval(self, state: SupportState) -> dict[str, Any]:
        call = state["tool_call"]
        response = interrupt(
            {
                "kind": "tool_approval",
                "tool_name": call["name"],
                "arguments": call["args"],
                "risk_level": "high",
                "description": "退款申请会修改订单状态并进入资金处理流程。",
            }
        )
        return {"approval_status": str(response.get("decision", "reject"))}

    def _execute(self, state: SupportState) -> dict[str, Any]:
        call = state["tool_call"]
        started = time.perf_counter()
        result, citations = execute_support_tool(
            call["name"],
            call["args"],
            state["user_id"],
            state["conversation_id"],
        )
        duration_ms = round((time.perf_counter() - started) * 1000)
        trace = {
            "tool": call["name"],
            "status": "completed",
            "duration_ms": duration_ms,
            "preview": result[:180],
        }
        with SessionLocal() as db:
            db.add(
                ToolExecution(
                    conversation_id=state["conversation_id"],
                    tool_name=call["name"],
                    arguments_json=json.dumps(call["args"], ensure_ascii=False),
                    result_preview=result[:500],
                    duration_ms=duration_ms,
                )
            )
            db.commit()
        return {"tool_result": result, "citations": citations, "traces": [trace]}

    def _compose(self, state: SupportState) -> dict[str, Any]:
        if state.get("approval_status") == "reject":
            return {"answer": "退款申请未获批准，订单状态未发生变化。需要进一步处理时，我可以为你转接人工客服。"}

        if self.settings.has_llm and state.get("tool_result"):
            try:
                model = ChatDeepSeek(
                    model=self.settings.deepseek_model,
                    api_key=self.settings.deepseek_api_key,
                    base_url=self.settings.deepseek_base_url,
                    temperature=0.2,
                )
                response = model.invoke(
                    [
                        SystemMessage(content="你是客服助手。仅根据工具结果简洁回答，禁止编造。"),
                        HumanMessage(
                            content=f"用户问题：{state['user_message']}\n工具结果：{state['tool_result']}"
                        ),
                    ]
                )
                return {"answer": str(response.content)}
            except Exception:
                pass
        return {"answer": _offline_answer(state.get("tool_call", {}), state.get("tool_result", ""))}


def _offline_plan(message: str) -> dict[str, Any]:
    order_match = re.search(r"RF\d{8,}", message.upper())
    order_id = order_match.group(0) if order_match else ""
    lowered = message.casefold()
    if any(word in message for word in ("退款", "退货", "退钱")) and order_id:
        return {"name": "request_refund", "args": {"order_id": order_id, "reason": message}}
    if any(word in message for word in ("物流", "快递", "到哪")) and order_id:
        return {"name": "track_shipment", "args": {"order_id": order_id}}
    if any(word in message for word in ("订单", "购买")) and order_id:
        return {"name": "get_order", "args": {"order_id": order_id}}
    if any(word in message for word in ("人工", "投诉", "盗用", "重复扣款")):
        return {"name": "handoff_to_human", "args": {"reason": message}}
    if any(word in message for word in ("故障", "坏了", "无法使用")):
        return {
            "name": "create_ticket",
            "args": {"subject": "产品故障", "description": message, "priority": "medium"},
        }
    return {"name": "search_support_knowledge", "args": {"query": lowered}}


def _offline_answer(call: dict[str, Any], result: str) -> str:
    name = call.get("name", "")
    try:
        payload = json.loads(result) if result else {}
    except json.JSONDecodeError:
        payload = result
    if name == "search_support_knowledge":
        if not payload:
            return "知识库中暂时没有找到直接相关的规则，我可以为你创建人工工单。"
        return "根据知识库：" + " ".join(item["content"] for item in payload[:2])
    if isinstance(payload, dict) and payload.get("error"):
        return payload["error"]
    if name == "get_order":
        return f"订单 {payload['order_id']} 为“{payload['product_name']}”，当前状态：{payload['status']}，金额 ¥{payload['amount']:.2f}。"
    if name == "track_shipment":
        return f"订单 {payload['order_id']} 的物流单号是 {payload['tracking_number']}。{payload['latest_event']}。"
    if name == "request_refund":
        return f"退款申请已提交：订单 {payload['order_id']}，金额 ¥{payload['amount']:.2f}。后续状态可在订单中心查看。"
    if name in {"create_ticket", "handoff_to_human"}:
        return f"已创建工单 {payload['ticket_id']}，优先级为 {payload['priority']}，人工客服会继续处理。"
    return "请求已经处理。"


runtime = SupportAgentRuntime()

