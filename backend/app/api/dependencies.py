import os
import logging
from functools import lru_cache
from typing import Optional
from fastapi import Depends
from qdrant_client import QdrantClient
from app.core.config import Settings, get_settings
from app.repositories.role_repository import RoleRepository
from app.repositories.vector_repository import VectorRepository
from app.services.chunking import TextChunker
from app.services.embedding import BaseEmbeddingService, FastEmbedService
from app.services.indexer import IndexingService
from app.services.search import SearchService


@lru_cache(maxsize=1)
def get_qdrant_client() -> QdrantClient:
    settings = get_settings()
    if settings.qdrant_url:
        return QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
        )
    if settings.qdrant_path:
        os.makedirs(settings.qdrant_path, exist_ok=True)
        return QdrantClient(path=settings.qdrant_path)
    return QdrantClient(location=":memory:")

def check_qdrant_connection() -> bool:
    try:
        get_qdrant_client()
        return True
    except Exception as e:
        logging.error(f"Qdrant Connection Check Failed {e}")
        return False


@lru_cache(maxsize=1)
def get_embedding_service() -> BaseEmbeddingService:
    settings = get_settings()
    return FastEmbedService(
        dense_model_name=settings.embedding_model_name,
        sparse_model_name=settings.sparse_model_name,
    )


@lru_cache(maxsize=1)
def get_role_repository() -> RoleRepository:
    settings = get_settings()
    dir_path = os.path.dirname(settings.sqlite_db_path)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)
    return RoleRepository(db_path=settings.sqlite_db_path)


@lru_cache(maxsize=1)
def get_vector_repository() -> VectorRepository:
    settings = get_settings()
    client = get_qdrant_client()
    embedding_service = get_embedding_service()
    return VectorRepository(
        client=client,
        collection_name=settings.collection_name,
        vector_size=embedding_service.dimension,
    )


@lru_cache(maxsize=1)
def get_text_chunker() -> TextChunker:
    settings = get_settings()
    return TextChunker(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )


def get_search_service(
    embedding_service: BaseEmbeddingService = Depends(get_embedding_service),
    vector_repo: VectorRepository = Depends(get_vector_repository),
    role_repo: RoleRepository = Depends(get_role_repository),
) -> SearchService:
    return SearchService(
        embedding_service=embedding_service,
        vector_repo=vector_repo,
        role_repo=role_repo,
    )


def get_indexing_service(
    role_repo: RoleRepository = Depends(get_role_repository),
    vector_repo: VectorRepository = Depends(get_vector_repository),
    embedding_service: BaseEmbeddingService = Depends(get_embedding_service),
    chunker: TextChunker = Depends(get_text_chunker),
) -> IndexingService:
    return IndexingService(
        role_repo=role_repo,
        vector_repo=vector_repo,
        embedding_service=embedding_service,
        chunker=chunker,
    )
