from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.routes import approvals, auth, conversations, knowledge, operations
from app.core.config import get_settings
from app.db.models import Base
from app.db.seed import seed_database
from app.db.session import SessionLocal, engine


settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    if engine.dialect.name == "postgresql":
        with engine.begin() as connection:
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.create_all(bind=engine)
    if engine.dialect.name == "postgresql":
        with engine.begin() as connection:
            connection.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS ix_knowledge_embedding_hnsw "
                    "ON knowledge_documents USING hnsw (embedding vector_cosine_ops)"
                )
            )
    with SessionLocal() as db:
        seed_database(db)
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="RAG + Tool Calling + Human-in-the-loop customer support agent",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in (auth.router, conversations.router, approvals.router, knowledge.router, operations.router):
    app.include_router(router, prefix=settings.api_prefix)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "mode": "llm" if settings.has_llm else "offline"}
