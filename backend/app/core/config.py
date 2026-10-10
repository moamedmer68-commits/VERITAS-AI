from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    app_name: str = "ResolveFlow API"
    app_env: str = "development"
    api_prefix: str = "/api/v1"
    database_url: str = f"sqlite:///{PROJECT_ROOT / 'resolveflow.db'}"
    redis_url: str = ""
    jwt_secret: str = "resolveflow-local-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 720
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-v4-flash"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    rag_top_k: int = 4
    rag_cache_seconds: int = 60

    model_config = SettingsConfigDict(
        env_file=(PROJECT_ROOT / ".env", PROJECT_ROOT.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def has_llm(self) -> bool:
        return bool(self.deepseek_api_key.strip())

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
