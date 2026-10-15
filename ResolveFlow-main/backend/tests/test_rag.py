from __future__ import annotations

from app.db.session import SessionLocal
from app.services.rag import embed_text, search_knowledge


def test_embedding_has_stable_dimension() -> None:
    embedding = embed_text("七天无理由退款")
    assert len(embedding) == 384
    assert any(value > 0 for value in embedding)


def test_local_rag_retrieves_refund_policy() -> None:
    with SessionLocal() as db:
        results = search_knowledge(db, "签收七天内可以退款吗")

    assert results
    assert any("退款" in result.content or "退货" in result.content for result in results)
