from abc import ABC, abstractmethod
from app.models.domain import SparseEmbedding
from typing import List

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
