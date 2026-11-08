import logging

from fastembed import SparseTextEmbedding, TextEmbedding

from app.models.domain import SparseEmbedding
from app.services.embedding.base import BaseEmbeddingService


logger = logging.getLogger(__name__)


class FastEmbedService(BaseEmbeddingService):
    def __init__(
        self,
        dense_model_name: str = "BAAI/bge-small-en-v1.5",
        sparse_model_name: str = "Qdrant/bm25",
        threads: int = 4,
    ):
        self.dense_model_name = dense_model_name
        self.sparse_model_name = sparse_model_name
        self.dense_model = TextEmbedding(model_name=dense_model_name, threads=threads)
        self.sparse_model = SparseTextEmbedding(model_name=sparse_model_name, threads=threads)

        probe_vector = next(iter(self.dense_model.embed(["probe"])))
        self._dimension = len(probe_vector)
        logger.info(
            "Embedding models initialized dense_model=%s sparse_model=%s dimension=%d",
            dense_model_name,
            sparse_model_name,
            self._dimension,
        )

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed_dense_documents(self, texts: list[str], batch_size: int = 256) -> list[list[float]]:
        if not texts:
            return []
        embeddings = list(self.dense_model.embed(texts, batch_size=batch_size))
        return [vec.tolist() for vec in embeddings]

    def embed_dense_query(self, text: str) -> list[float]:
        generator = self.dense_model.embed([text])
        vector = next(iter(generator))
        return vector.tolist()

    def embed_sparse_documents(self, texts: list[str], batch_size: int = 256) -> list[SparseEmbedding]:
        if not texts:
            return []
        embeddings = list(self.sparse_model.embed(texts, batch_size=batch_size))
        return [
            SparseEmbedding(
                indices=item.indices.tolist(),
                values=[float(v) for v in item.values.tolist()],
            )
            for item in embeddings
        ]

    def embed_sparse_query(self, text: str) -> SparseEmbedding:
        generator = self.sparse_model.embed([text])
        item = next(iter(generator))
        return SparseEmbedding(
            indices=item.indices.tolist(),
            values=[float(v) for v in item.values.tolist()],
        )
