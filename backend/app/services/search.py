import heapq
import logging

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


logger = logging.getLogger(__name__)


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
    ) -> SearchResponse:
        cleaned_query = query.strip()
        if not cleaned_query:
            logger.warning("Search skipped because query was empty")
            return SearchResponse(query=query, total=0, results=[])

        logger.debug("Starting hybrid search top_k=%d offset=%d", top_k, offset)
        dense_vector = self.embedding_service.embed_dense_query(cleaned_query)
        sparse_vector = self.embedding_service.embed_sparse_query(cleaned_query)

        oversample_limit = max((top_k + offset) * 3, 30)
        hits = self.vector_repo.search_hybrid(
            dense_vector=dense_vector,
            sparse_vector=sparse_vector,
            limit=oversample_limit,
        )
        logger.debug("Hybrid search returned chunk_hits=%d", len(hits))

        best_chunks_by_role: dict[str, VectorHit] = {}
        for hit in hits:
            role_no = hit.role_number
            if not role_no:
                continue
            if role_no not in best_chunks_by_role or hit.score > best_chunks_by_role[role_no].score:
                best_chunks_by_role[role_no] = hit

        total_roles = len(best_chunks_by_role)
        selected_hits = heapq.nlargest(
            offset + top_k,
            best_chunks_by_role.values(),
            key=lambda h: h.score,
        )
        paged_hits = selected_hits[offset:]
        logger.info(
            "Search completed candidate_roles=%d returned_roles=%d top_k=%d offset=%d",
            total_roles,
            len(paged_hits),
            top_k,
            offset,
        )

        role_numbers = [h.role_number for h in paged_hits]
        roles_map = self.role_repo.get_roles_batch(role_numbers)

        results: list[SearchResultItem] = []
        for index, hit in enumerate(paged_hits):
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
                    rank=offset + index + 1,
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
            logger.info("Role description not found role_number=%s", role_number)
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

    def get_role_detail(self, role_number: str) -> RoleDetailResponse | None:
        record = self.role_repo.get_by_role_number(role_number.strip())
        if record is None:
            logger.info("Role detail not found role_number=%s", role_number)
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
