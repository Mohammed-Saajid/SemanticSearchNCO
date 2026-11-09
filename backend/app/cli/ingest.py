import argparse
import asyncio
import logging
import sys

from qdrant_client import AsyncQdrantClient

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.repositories.role_repository import RoleRepository
from app.repositories.vector_repository import VectorRepository
from app.services.chunking import TextChunker
from app.services.embedding import FastEmbedService
from app.services.indexer import IndexingService


async def run_ingest(json_path: str, batch_size: int = 64) -> None:
    settings = get_settings()
    logger = setup_logging(debug=settings.debug)

    logger.info(
        "Initializing repositories and embedding models: %s (dense) and %s (sparse)",
        settings.embedding_model_name,
        settings.sparse_model_name,
    )
    embedding_service = FastEmbedService(
        dense_model_name=settings.embedding_model_name,
        sparse_model_name=settings.sparse_model_name,
    )

    if settings.qdrant_url:
        qdrant_client = AsyncQdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
    elif settings.qdrant_path:
        qdrant_client = AsyncQdrantClient(path=settings.qdrant_path)
    else:
        qdrant_client = AsyncQdrantClient(location=":memory:")

    vector_repo = VectorRepository(
        client=qdrant_client,
        collection_name=settings.collection_name,
        vector_size=embedding_service.dimension,
    )
    role_repo = RoleRepository(db_path=settings.sqlite_db_path)
    chunker = TextChunker(chunk_size=settings.chunk_size, chunk_overlap=settings.chunk_overlap)

    indexer = IndexingService(
        role_repo=role_repo,
        vector_repo=vector_repo,
        embedding_service=embedding_service,
        chunker=chunker,
    )

    logger.info("Ingesting data from %s", json_path)
    stats = await indexer.index_from_file(json_path, batch_size=batch_size)
    logger.info(
        "Ingestion completed. Indexed %d roles and %d chunks.",
        stats["indexed_roles"],
        stats["indexed_chunks"],
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest occupational roles into Qdrant and SQLite")
    parser.add_argument(
        "--json-path",
        type=str,
        default="backend/data/json/formatted.json",
        help="Path to formatted JSON file",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=64,
        help="Batch size for embeddings and upserts",
    )
    args = parser.parse_args()

    try:
        asyncio.run(run_ingest(json_path=args.json_path, batch_size=args.batch_size))
    except Exception:
        logging.getLogger(__name__).exception("Ingestion failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
