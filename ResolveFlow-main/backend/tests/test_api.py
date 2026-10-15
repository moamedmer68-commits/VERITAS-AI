from __future__ import annotations

import os

os.environ["DEEPSEEK_API_KEY"] = ""

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.models import Order
from app.db.session import SessionLocal
from app.main import app


def login(client: TestClient, email: str, password: str) -> dict[str, str]:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def create_conversation(client: TestClient, headers: dict[str, str]) -> str:
    response = client.post("/api/v1/conversations", headers=headers, json={"title": "API test"})
    assert response.status_code == 200
    return response.json()["id"]


def test_health_login_and_order_tool() -> None:
    with TestClient(app) as client:
        assert client.get("/health").json() == {"status": "ok", "mode": "offline"}
        headers = login(client, "customer@resolveflow.dev", "customer123")
        conversation_id = create_conversation(client, headers)
        response = client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            headers=headers,
            json={"content": "查询订单 RF20260801001"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "offline"
    assert payload["traces"][0]["tool"] == "get_order"
    assert "RF20260801001" in payload["answer"]


def test_sse_stream_contains_structured_events() -> None:
    with TestClient(app) as client:
        headers = login(client, "customer@resolveflow.dev", "customer123")
        conversation_id = create_conversation(client, headers)
        response = client.post(
            f"/api/v1/conversations/{conversation_id}/messages/stream",
            headers=headers,
            json={"content": "查询订单 RF20260801001"},
        )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert "event: status" in response.text
    assert "event: tool" in response.text
    assert "event: message" in response.text
    assert "event: done" in response.text


def test_refund_requires_and_resumes_human_approval() -> None:
    with SessionLocal() as db:
        order = db.scalar(select(Order).where(Order.id == "RF20260801001"))
        assert order is not None
        order.status = "shipped"
        db.commit()

    try:
        with TestClient(app) as client:
            customer_headers = login(client, "customer@resolveflow.dev", "customer123")
            admin_headers = login(client, "admin@resolveflow.dev", "admin123")
            conversation_id = create_conversation(client, customer_headers)
            request = client.post(
                f"/api/v1/conversations/{conversation_id}/messages",
                headers=customer_headers,
                json={"content": "请为订单 RF20260801001 申请退款"},
            )
            approval_id = request.json()["pending_approval_id"]

            assert request.status_code == 200
            assert approval_id
            with SessionLocal() as db:
                assert db.get(Order, "RF20260801001").status == "shipped"

            decision = client.post(
                f"/api/v1/approvals/{approval_id}/decision",
                headers=admin_headers,
                json={"decision": "approve", "note": "自动化测试批准"},
            )

        assert decision.status_code == 200
        assert decision.json()["traces"][0]["tool"] == "request_refund"
        with SessionLocal() as db:
            assert db.get(Order, "RF20260801001").status == "refund_requested"
    finally:
        with SessionLocal() as db:
            order = db.get(Order, "RF20260801001")
            if order is not None:
                order.status = "shipped"
                db.commit()
