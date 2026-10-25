from typing import Dict, List, Optional

from app.models.domain import RoleRecord, VectorHit
from app.models.schemas import (
    RoleDescriptionResponse,
    RoleDetailResponse,
    SearchResponse,
    SearchResultItem,
)
from app.repositories.role_repository import RoleRepository
from app.repositories.vector_repository import VectorRepository
from app.services.embedding import BaseEmbeddingService


class SearchService:
    def __init__(
        self,
        embedding_service: BaseEmbeddingService,
        vector_repo: VectorRepository,
        role_repo: RoleRepository,
    ):
        self.embedding_service = embedding_service
        self.vector_repo = vector_repo
        self.role_repo = role_repo

    def search(
        self,
        query: str,
        top_k: int = 10,
        offset: int = 0,
        bm25_weight: float = 0.4,
        vector_weight: float = 0.6,
    ) -> SearchResponse:
        cleaned_query = query.strip()
        if not cleaned_query:
            return SearchResponse(query=query, total=0, results=[])

        dense_vector = self.embedding_service.embed_dense_query(cleaned_query)
        sparse_vector = self.embedding_service.embed_sparse_query(cleaned_query)

        oversample_limit = max((top_k + offset) * 3, 30)
        hits = self.vector_repo.search_hybrid(
            dense_vector=dense_vector,
            sparse_vector=sparse_vector,
            limit=oversample_limit,
        )

        best_chunks_by_role: Dict[str, VectorHit] = {}
        for hit in hits:
            role_no = hit.role_number
            if not role_no:
                continue
            if role_no not in best_chunks_by_role or hit.score > best_chunks_by_role[role_no].score:
                best_chunks_by_role[role_no] = hit

        total_roles = len(best_chunks_by_role)
        sorted_hits = sorted(
            best_chunks_by_role.values(),
            key=lambda h: h.score,
            reverse=True,
        )
        paged_hits = sorted_hits[offset : offset + top_k]

        role_numbers = [h.role_number for h in paged_hits]
        roles_map = self.role_repo.get_roles_batch(role_numbers)

        results: List[SearchResultItem] = []
        for hit in paged_hits:
            role_rec = roles_map.get(
                hit.role_number,
                RoleRecord(
                    role_number=hit.role_number,
                    title="Unknown Role",
                    old_regulation="",
                    description="",
                    division="",
                    sub_division="",
                    group="",
                    family="",
                ),
            )
            results.append(
                SearchResultItem(
                    id=hit.chunk_id,
                    role_number=hit.role_number,
                    role_title=role_rec.title,
                    chunk_index=hit.chunk_index,
                    chunk_text=hit.text,
                    score=hit.score,
                    combined_score=hit.score,
                    occupational_title=role_rec.title,
                    nco_2015=role_rec.role_number,
                    nco_2004=role_rec.old_regulation,
                    division=role_rec.division,
                    sub_division=role_rec.sub_division,
                    group=role_rec.group,
                    family=role_rec.family,
                    bm25_score=hit.score,
                    vector_score=hit.score,
                )
            )

        return SearchResponse(
            query=cleaned_query,
            total=total_roles,
            results=results,
        )

    def get_role_description(self, role_number: str) -> RoleDescriptionResponse:
        record = self.role_repo.get_by_role_number(role_number.strip())
        if record is None:
            return RoleDescriptionResponse(
                description="Role not found",
                role_number=role_number,
                title=None,
            )
        return RoleDescriptionResponse(
            description=record.description,
            role_number=record.role_number,
            title=record.title,
        )

    def get_role_detail(self, role_number: str) -> Optional[RoleDetailResponse]:
        record = self.role_repo.get_by_role_number(role_number.strip())
        if record is None:
            return None
        return RoleDetailResponse(
            role_number=record.role_number,
            title=record.title,
            old_regulation=record.old_regulation,
            division=record.division,
            sub_division=record.sub_division,
            group=record.group,
            family=record.family,
            description=record.description,
        )
