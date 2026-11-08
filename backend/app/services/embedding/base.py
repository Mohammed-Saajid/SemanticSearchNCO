from abc import ABC, abstractmethod

from app.models.domain import SparseEmbedding


class BaseEmbeddingService(ABC):
    @abstractmethod
    def embed_dense_documents(self, texts: list[str], batch_size: int = 256) -> list[list[float]]:
        pass

    @abstractmethod
    def embed_dense_query(self, text: str) -> list[float]:
        pass

    @abstractmethod
    def embed_sparse_documents(self, texts: list[str], batch_size: int = 256) -> list[SparseEmbedding]:
        pass

    @abstractmethod
    def embed_sparse_query(self, text: str) -> SparseEmbedding:
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        pass
