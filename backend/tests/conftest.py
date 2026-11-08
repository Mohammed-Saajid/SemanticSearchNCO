import os
import sys
import tempfile
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from qdrant_client import QdrantClient


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.api.dependencies import (
    get_role_repository,
    get_search_service,
    get_settings,
    get_vector_repository,
)
from app.core.config import Settings
from app.main import create_app
from app.models.domain import RoleRecord, SparseEmbedding
from app.repositories.role_repository import RoleRepository
from app.repositories.vector_repository import VectorRepository
from app.services.chunking import TextChunker
from app.services.embedding import BaseEmbeddingService
from app.services.indexer import IndexingService
from app.services.search import SearchService


class DummyEmbeddingService(BaseEmbeddingService):
    def __init__(self, dimension: int = 8):
        self._dim = dimension

    @property
    def dimension(self) -> int:
        return self._dim

    def _hash_vector(self, text: str) -> list[float]:
        val = sum(ord(c) for c in text)
        vec = [(val % (i + 3)) / (i + 3) for i in range(self._dim)]
        norm = sum(x * x for x in vec) ** 0.5 or 1.0
        return [round(x / norm, 6) for x in vec]

    def _hash_sparse(self, text: str) -> SparseEmbedding:
        val = sum(ord(c) for c in text)
        idx1 = (val % 50) + 1
        idx2 = ((val * 3) % 50) + 1
        return SparseEmbedding(indices=[idx1, idx2], values=[1.2, 0.8])

    def embed_dense_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._hash_vector(t) for t in texts]

    def embed_dense_query(self, text: str) -> list[float]:
        return self._hash_vector(text)

    def embed_sparse_documents(self, texts: list[str]) -> list[SparseEmbedding]:
        return [self._hash_sparse(t) for t in texts]

    def embed_sparse_query(self, text: str) -> SparseEmbedding:
        return self._hash_sparse(text)


@pytest.fixture
def dummy_embedding_service() -> BaseEmbeddingService:
    return DummyEmbeddingService(dimension=8)


@pytest.fixture
def temp_db_path() -> Generator[str, None, None]:
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    yield path
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def test_settings(temp_db_path: str) -> Settings:
    return Settings(
        app_name="Test Semantic Search",
        app_version="0.0.1",
        debug=True,
        sqlite_db_path=temp_db_path,
        qdrant_path=None,
        qdrant_url=None,
        collection_name="test_collection",
        embedding_dimension=8,
    )


@pytest.fixture
def role_repository(temp_db_path: str) -> RoleRepository:
    return RoleRepository(db_path=temp_db_path)


@pytest.fixture
def in_memory_qdrant() -> QdrantClient:
    return QdrantClient(location=":memory:")


@pytest.fixture
def vector_repository(
    in_memory_qdrant: QdrantClient,
    test_settings: Settings,
    dummy_embedding_service: BaseEmbeddingService,
) -> VectorRepository:
    return VectorRepository(
        client=in_memory_qdrant,
        collection_name=test_settings.collection_name,
        vector_size=dummy_embedding_service.dimension,
    )


@pytest.fixture
def text_chunker(test_settings: Settings) -> TextChunker:
    return TextChunker(
        chunk_size=test_settings.chunk_size,
        chunk_overlap=test_settings.chunk_overlap,
    )


@pytest.fixture
def search_service(
    dummy_embedding_service: BaseEmbeddingService,
    vector_repository: VectorRepository,
    role_repository: RoleRepository,
) -> SearchService:
    return SearchService(
        embedding_service=dummy_embedding_service,
        vector_repo=vector_repository,
        role_repo=role_repository,
    )


@pytest.fixture
def indexing_service(
    role_repository: RoleRepository,
    vector_repository: VectorRepository,
    dummy_embedding_service: BaseEmbeddingService,
    text_chunker: TextChunker,
) -> IndexingService:
    return IndexingService(
        role_repo=role_repository,
        vector_repo=vector_repository,
        embedding_service=dummy_embedding_service,
        chunker=text_chunker,
    )


@pytest.fixture
def sample_roles() -> list[RoleRecord]:
    return [
        RoleRecord(
            role_number="1001.0100",
            title="Software Architect",
            old_regulation="1001.1",
            description="Designs and governs software systems architecture and patterns.",
            division="Information Technology",
            sub_division="Software Engineering",
            group="Architecture",
            family="Software Architecture",
        ),
        RoleRecord(
            role_number="1001.0200",
            title="Data Scientist",
            old_regulation="1001.2",
            description="Builds machine learning models and conducts statistical analytics.",
            division="Information Technology",
            sub_division="Data & AI",
            group="Analytics",
            family="Data Science",
        ),
        RoleRecord(
            role_number="1001.0300",
            title="Database Administrator",
            old_regulation="1001.3",
            description="Manages database schemas, performance, security, and backups.",
            division="Information Technology",
            sub_division="Infrastructure",
            group="Databases",
            family="DB Administration",
        ),
    ]


@pytest.fixture
def test_client(
    test_settings: Settings,
    search_service: SearchService,
    vector_repository: VectorRepository,
    role_repository: RoleRepository,
) -> TestClient:
    app = create_app(settings=test_settings)

    app.dependency_overrides[get_settings] = lambda: test_settings
    app.dependency_overrides[get_search_service] = lambda: search_service
    app.dependency_overrides[get_vector_repository] = lambda: vector_repository
    app.dependency_overrides[get_role_repository] = lambda: role_repository

    return TestClient(app)
