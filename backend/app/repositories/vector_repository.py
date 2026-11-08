import logging
import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    Fusion,
    FusionQuery,
    PointStruct,
    Prefetch,
    SparseVector,
    SparseVectorParams,
    VectorParams,
)

from app.models.domain import RoleChunk, SparseEmbedding, VectorHit


logger = logging.getLogger(__name__)


class VectorRepository:
    def __init__(
        self,
        client: QdrantClient,
        collection_name: str,
        vector_size: int,
    ):
        self.client = client
        self.collection_name = collection_name
        self.vector_size = vector_size
        self.ensure_collection()

    def ensure_collection(self) -> None:
        collections_response = self.client.get_collections()
        existing = [c.name for c in collections_response.collections]
        needs_creation = self.collection_name not in existing

        if not needs_creation:
            info = self.client.get_collection(self.collection_name)
            vectors = info.config.params.vectors
            sparse = info.config.params.sparse_vectors
            if not isinstance(vectors, dict) or "dense" not in vectors or not sparse:
                logger.warning(
                    "Replacing incompatible Qdrant collection collection=%s",
                    self.collection_name,
                )
                self.client.delete_collection(self.collection_name)
                needs_creation = True

        if needs_creation:
            logger.info(
                "Creating Qdrant collection collection=%s vector_size=%d",
                self.collection_name,
                self.vector_size,
            )
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config={
                    "dense": VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE,
                    )
                },
                sparse_vectors_config={"sparse": SparseVectorParams()},
            )

    def _to_uuid(self, identifier: str) -> str:
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, identifier))

    def upsert_chunks(
        self,
        chunks: list[RoleChunk],
        dense_embeddings: list[list[float]],
        sparse_embeddings: list[SparseEmbedding],
        batch_size: int = 128,
    ) -> int:
        if not (len(chunks) == len(dense_embeddings) == len(sparse_embeddings)):
            raise ValueError("Chunks, dense embeddings, and sparse embeddings counts must match")
        if not chunks:
            logger.debug("Skipping empty vector upsert collection=%s", self.collection_name)
            return 0

        total_upserted = 0
        for i in range(0, len(chunks), batch_size):
            chunk_batch = chunks[i : i + batch_size]
            dense_batch = dense_embeddings[i : i + batch_size]
            sparse_batch = sparse_embeddings[i : i + batch_size]

            points: list[PointStruct] = []
            for chunk, dense_vec, sparse_vec in zip(chunk_batch, dense_batch, sparse_batch, strict=False):
                points.append(
                    PointStruct(
                        id=self._to_uuid(chunk.chunk_id),
                        vector={
                            "dense": dense_vec,
                            "sparse": SparseVector(
                                indices=sparse_vec.indices,
                                values=sparse_vec.values,
                            ),
                        },
                        payload={
                            "chunk_id": chunk.chunk_id,
                            "role_number": chunk.role_number,
                            "chunk_index": chunk.chunk_index,
                            "text": chunk.text,
                        },
                    )
                )

            self.client.upsert(
                collection_name=self.collection_name,
                points=points,
                wait=True,
            )
            total_upserted += len(points)
            logger.debug(
                "Upserted vector batch collection=%s batch_size=%d total_upserted=%d",
                self.collection_name,
                len(points),
                total_upserted,
            )

        logger.info(
            "Vector upsert completed collection=%s points=%d",
            self.collection_name,
            total_upserted,
        )
        return total_upserted

    def search_hybrid(
        self,
        dense_vector: list[float],
        sparse_vector: SparseEmbedding,
        limit: int = 10,
    ) -> list[VectorHit]:
        sparse_q = SparseVector(
            indices=sparse_vector.indices,
            values=sparse_vector.values,
        )

        response = self.client.query_points(
            collection_name=self.collection_name,
            prefetch=[
                Prefetch(
                    query=dense_vector,
                    using="dense",
                    limit=limit * 2,
                ),
                Prefetch(
                    query=sparse_q,
                    using="sparse",
                    limit=limit * 2,
                ),
            ],
            query=FusionQuery(fusion=Fusion.RRF),
            limit=limit,
            with_payload=True,
        )
        logger.debug(
            "Qdrant hybrid query completed collection=%s limit=%d hits=%d",
            self.collection_name,
            limit,
            len(response.points),
        )

        hits: list[VectorHit] = []
        for point in response.points:
            payload = point.payload or {}
            hits.append(
                VectorHit(
                    chunk_id=payload.get("chunk_id", str(point.id)),
                    role_number=payload.get("role_number", ""),
                    chunk_index=payload.get("chunk_index", 0),
                    text=payload.get("text", ""),
                    score=float(point.score),
                )
            )
        return hits

    def count(self) -> int:
        try:
            info = self.client.get_collection(self.collection_name)
            return info.points_count or 0
        except Exception:
            logger.exception(
                "Unable to count Qdrant collection collection=%s",
                self.collection_name,
            )
            return 0
