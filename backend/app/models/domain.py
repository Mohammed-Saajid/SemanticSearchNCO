from dataclasses import dataclass


@dataclass(frozen=True)
class SparseEmbedding:
    indices: list[int]
    values: list[float]


@dataclass(frozen=True)
class RoleRecord:
    role_number: str
    title: str
    old_regulation: str
    description: str
    division: str = ""
    sub_division: str = ""
    group: str = ""
    family: str = ""


@dataclass(frozen=True)
class RoleChunk:
    chunk_id: str
    role_number: str
    chunk_index: int
    text: str


@dataclass(frozen=True)
class VectorHit:
    chunk_id: str
    role_number: str
    chunk_index: int
    text: str
    score: float
    role_title: str | None = None
    dense_score: float | None = None
    sparse_score: float | None = None
