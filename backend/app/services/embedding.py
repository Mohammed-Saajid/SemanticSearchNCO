from abc import ABC, abstractmethod
from typing import List
from fastembed import SparseTextEmbedding, TextEmbedding
from app.models.domain import SparseEmbedding


class BaseEmbeddingService(ABC):
    @abstractmethod
    def embed_dense_documents(self, texts: List[str], batch_size: int = 256) -> List[List[float]]:
        pass

    @abstractmethod
    def embed_dense_query(self, text: str) -> List[float]:
        pass

    @abstractmethod
    def embed_sparse_documents(self, texts: List[str], batch_size: int = 256) -> List[SparseEmbedding]:
        pass

    @abstractmethod
    def embed_sparse_query(self, text: str) -> SparseEmbedding:
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        pass


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

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed_dense_documents(self, texts: List[str], batch_size: int = 256) -> List[List[float]]:
        if not texts:
            return []
        embeddings = list(self.dense_model.embed(texts, batch_size=batch_size))
        return [vec.tolist() for vec in embeddings]

    def embed_dense_query(self, text: str) -> List[float]:
        generator = self.dense_model.embed([text])
        vector = next(iter(generator))
        return vector.tolist()

    def embed_sparse_documents(self, texts: List[str], batch_size: int = 256) -> List[SparseEmbedding]:
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

