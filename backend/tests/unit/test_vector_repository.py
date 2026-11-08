import pytest

from app.models.domain import RoleChunk, SparseEmbedding
from app.repositories.vector_repository import VectorRepository


def test_upsert_length_mismatch(vector_repository: VectorRepository):
    chunks = [RoleChunk("c1", "1001.0100", 0, "sample text")]
    with pytest.raises(ValueError):
        vector_repository.upsert_chunks(chunks, [], [])


def test_upsert_empty(vector_repository: VectorRepository):
    assert vector_repository.upsert_chunks([], [], []) == 0


def test_upsert_and_hybrid_search(vector_repository: VectorRepository):
    chunks = [
        RoleChunk("c1", "1001.0100", 0, "software development and programming"),
        RoleChunk("c2", "1001.0200", 0, "machine learning algorithms and data science"),
    ]
    dense_embeddings = [
        [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    ]
    sparse_embeddings = [
        SparseEmbedding(indices=[10, 20], values=[1.5, 2.0]),
        SparseEmbedding(indices=[30, 40], values=[1.1, 2.3]),
    ]

    upserted = vector_repository.upsert_chunks(chunks, dense_embeddings, sparse_embeddings)
    assert upserted == 2
    assert vector_repository.count() == 2

    query_dense = [0.9, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    query_sparse = SparseEmbedding(indices=[10, 20], values=[1.0, 1.0])
    hits = vector_repository.search_hybrid(query_dense, query_sparse, limit=2)
    assert len(hits) >= 1
    assert hits[0].chunk_id == "c1"
    assert hits[0].role_number == "1001.0100"
