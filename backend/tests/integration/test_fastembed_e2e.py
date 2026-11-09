import pytest
from qdrant_client import QdrantClient

from app.repositories.role_repository import RoleRepository
from app.repositories.vector_repository import VectorRepository
from app.services.chunking import TextChunker
from app.services.embedding import FastEmbedService
from app.services.indexer import IndexingService
from app.services.search import SearchService


@pytest.mark.asyncio
async def test_fastembed_hybrid_indexing_and_search(temp_db_path: str):
    role_repo = RoleRepository(db_path=temp_db_path)
    client = QdrantClient(location=":memory:")
    embedding_service = FastEmbedService(
        dense_model_name="BAAI/bge-small-en-v1.5",
        sparse_model_name="Qdrant/bm25",
    )
    vector_repo = VectorRepository(
        client=client,
        collection_name="e2e_hybrid_collection",
        vector_size=embedding_service.dimension,
    )
    chunker = TextChunker(chunk_size=100, chunk_overlap=20)
    indexer = IndexingService(
        role_repo=role_repo,
        vector_repo=vector_repo,
        embedding_service=embedding_service,
        chunker=chunker,
    )

    data = [
        {
            "role_number": "1111.0100",
            "Role Name": "Elected Official Union Government",
            "Role Description": "Serves in legislative and executive branches of government, presides over parliament and shapes policy.",
        },
        {
            "role_number": "2141.0100",
            "Role Name": "Computer Software Engineer",
            "Role Description": "Researches, analyzes, designs and develops software programming applications and operating systems.",
        },
    ]

    await indexer.index_data(data)

    searcher = SearchService(
        embedding_service=embedding_service,
        vector_repo=vector_repo,
        role_repo=role_repo,
    )

    result = await searcher.search("software programming developer", top_k=2)
    assert result.total >= 1
    assert result.results[0].role_number == "2141.0100"
    assert "Software Engineer" in result.results[0].role_title
