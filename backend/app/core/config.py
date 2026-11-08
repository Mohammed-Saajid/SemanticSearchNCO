from functools import lru_cache

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Semantic Search API"
    app_version: str = "2.0.0"
    debug: bool = False
    environment: str = "development"

    # Required for container and LAN access; deployments may override HOST.
    host: str = "0.0.0.0"  # nosec B104
    port: int = Field(default=8000, validation_alias=AliasChoices("PORT", "APP_PORT"))

    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "*",
        ]
    )

    sqlite_db_path: str = "db/roles.db"
    qdrant_path: str | None = "db/qdrant_storage"
    qdrant_url: str | None = None
    qdrant_api_key: str | None = None
    collection_name: str = "nco_roles"

    embedding_model_name: str = "BAAI/bge-small-en-v1.5"
    sparse_model_name: str = "Qdrant/bm25"
    embedding_dimension: int = 384

    chunk_size: int = 250
    chunk_overlap: int = 50
    default_top_k: int = 10
    max_top_k: int = 100

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, value: object) -> bool:
        if isinstance(value, str):
            return value.strip().lower() in ("1", "true", "yes", "on", "debug")
        return bool(value)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
