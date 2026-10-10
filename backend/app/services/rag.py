from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from redis import Redis
from sklearn.feature_extraction.text import HashingVectorizer, TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import KnowledgeDocument


@dataclass(frozen=True)
class RetrievedDocument:
    title: str
    source: str
    content: str
    score: float


def embed_text(text: str) -> list[float]:
    vectorizer = HashingVectorizer(
        analyzer="char",
        ngram_range=(2, 4),
        n_features=384,
        alternate_sign=False,
        norm="l2",
    )
    return vectorizer.transform([text]).toarray()[0].astype(float).tolist()


def search_knowledge(db: Session, query: str, top_k: int = 4) -> list[RetrievedDocument]:
    cached = _cache_get(query, top_k)
    if cached is not None:
        return cached

    if db.bind is not None and db.bind.dialect.name == "postgresql":
        query_vector = embed_text(query)
        distance = KnowledgeDocument.embedding.cosine_distance(query_vector).label("distance")
        rows = db.execute(
            select(KnowledgeDocument, distance)
            .where(KnowledgeDocument.status == "indexed", KnowledgeDocument.embedding.is_not(None))
            .order_by(distance)
            .limit(top_k)
        ).all()
        results = [
            RetrievedDocument(
                title=document.title,
                source=document.source,
                content=document.content,
                score=max(0.0, 1.0 - float(row_distance)),
            )
            for document, row_distance in rows
        ]
        _cache_set(query, top_k, results)
        return results

    documents = list(db.scalars(select(KnowledgeDocument).where(KnowledgeDocument.status == "indexed")))
    if not documents or not query.strip():
        return []

    corpus = [document.content for document in documents]
    vectorizer = TfidfVectorizer(analyzer="char", ngram_range=(2, 4), sublinear_tf=True)
    matrix = vectorizer.fit_transform([*corpus, query])
    scores = cosine_similarity(matrix[-1], matrix[:-1])[0]
    ranked = scores.argsort()[::-1][:top_k]
    results = [
        RetrievedDocument(
            title=documents[index].title,
            source=documents[index].source,
            content=documents[index].content,
            score=float(scores[index]),
        )
        for index in ranked
        if scores[index] > 0
    ]
    _cache_set(query, top_k, results)
    return results


def _cache_key(query: str, top_k: int) -> str:
    digest = hashlib.sha256(f"{top_k}:{query}".encode()).hexdigest()
    return f"resolveflow:rag:{digest}"


def _redis_client() -> Redis | None:
    url = get_settings().redis_url.strip()
    return Redis.from_url(url, decode_responses=True, socket_timeout=0.2) if url else None


def _cache_get(query: str, top_k: int) -> list[RetrievedDocument] | None:
    client = _redis_client()
    if client is None:
        return None
    try:
        value = client.get(_cache_key(query, top_k))
        return [RetrievedDocument(**item) for item in json.loads(value)] if value else None
    except Exception:
        return None


def _cache_set(query: str, top_k: int, results: list[RetrievedDocument]) -> None:
    client = _redis_client()
    if client is None:
        return
    try:
        client.setex(
            _cache_key(query, top_k),
            get_settings().rag_cache_seconds,
            json.dumps([item.__dict__ for item in results], ensure_ascii=False),
        )
    except Exception:
        return
