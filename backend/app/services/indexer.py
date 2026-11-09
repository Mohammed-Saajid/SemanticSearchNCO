import json
import logging
import re
from typing import Any

from app.models.domain import RoleChunk, RoleRecord, SparseEmbedding
from app.repositories.role_repository import RoleRepository
from app.repositories.vector_repository import VectorRepository
from app.services.chunking import TextChunker
from app.services.embedding import BaseEmbeddingService


logger = logging.getLogger(__name__)


class IndexingService:
    def __init__(
        self,
        role_repo: RoleRepository,
        vector_repo: VectorRepository,
        embedding_service: BaseEmbeddingService,
        chunker: TextChunker,
    ):
        self.role_repo = role_repo
        self.vector_repo = vector_repo
        self.embedding_service = embedding_service
        self.chunker = chunker
        self._role_code_pattern = re.compile(r"^\d{4}\.\d{4}$")

    def _traverse_hierarchy(
        self,
        node: Any,
        roles: list[RoleRecord],
        chunks: list[RoleChunk],
        division: str = "",
        sub_division: str = "",
        group: str = "",
        family: str = "",
    ) -> None:
        if isinstance(node, dict):
            if "Division Name" in node:
                division = str(node["Division Name"]).strip()
            if "Sub-Division Name" in node:
                sub_division = str(node["Sub-Division Name"]).strip()
            if "Group Name" in node:
                group = str(node["Group Name"]).strip()
            if "Family Name" in node:
                family = str(node["Family Name"]).strip()

            for key, val in node.items():
                if self._role_code_pattern.match(key) and isinstance(val, dict):
                    role_num = key.strip()
                    title = str(val.get("Role Name", val.get("title", ""))).strip()
                    old_reg = str(val.get("2004 regulation", val.get("2004 Regulation", val.get("old_regulation", "")))).strip()
                    desc = str(val.get("Role Description", val.get("description", ""))).strip()
                    if desc:
                        roles.append(
                            RoleRecord(
                                role_number=role_num,
                                title=title if title else role_num,
                                old_regulation=old_reg,
                                division=division,
                                sub_division=sub_division,
                                group=group,
                                family=family,
                                description=desc,
                            )
                        )
                        chunks.extend(self.chunker.chunk_role(role_num, desc))
                elif isinstance(val, dict):
                    self._traverse_hierarchy(val, roles, chunks, division, sub_division, group, family)

    def parse_raw_data(self, raw_data: Any) -> tuple[list[RoleRecord], list[RoleChunk]]:
        roles: list[RoleRecord] = []
        chunks: list[RoleChunk] = []

        if isinstance(raw_data, list):
            for item in raw_data:
                role_num = str(item.get("role_number", "")).strip()
                title = str(item.get("Role Name", item.get("title", item.get("Occupational Title", "")))).strip()
                old_reg = str(item.get("2004 Regulation", item.get("2004 regulation", item.get("old_regulation", item.get("NCO 2004", ""))))).strip()
                division = str(item.get("Division", item.get("division", ""))).strip()
                sub_division = str(item.get("Sub Division", item.get("sub_division", ""))).strip()
                group = str(item.get("Group", item.get("group", ""))).strip()
                family = str(item.get("Family", item.get("family", ""))).strip()
                desc = str(item.get("Role Description", item.get("description", ""))).strip()

                if not role_num or not desc:
                    continue

                roles.append(
                    RoleRecord(
                        role_number=role_num,
                        title=title if title else role_num,
                        old_regulation=old_reg,
                        division=division,
                        sub_division=sub_division,
                        group=group,
                        family=family,
                        description=desc,
                    )
                )
                chunks.extend(self.chunker.chunk_role(role_num, desc))

        elif isinstance(raw_data, dict):
            first_key = next(iter(raw_data.keys()), "") if raw_data else ""
            if first_key.isdigit():
                self._traverse_hierarchy(raw_data, roles, chunks)
            else:
                for role_num, content in raw_data.items():
                    role_num_str = str(role_num).strip()
                    if isinstance(content, dict):
                        title = str(content.get("Role Name", content.get("title", ""))).strip()
                        old_reg = str(content.get("2004 Regulation", content.get("2004 regulation", ""))).strip()
                        division = str(content.get("Division", content.get("division", ""))).strip()
                        sub_division = str(content.get("Sub Division", content.get("sub_division", ""))).strip()
                        group = str(content.get("Group", content.get("group", ""))).strip()
                        family = str(content.get("Family", content.get("family", ""))).strip()
                        desc = str(content.get("Role Description", content.get("description", ""))).strip()
                    else:
                        title = role_num_str
                        old_reg = ""
                        division = ""
                        sub_division = ""
                        group = ""
                        family = ""
                        desc = str(content).strip()

                    if not role_num_str or not desc:
                        continue

                    roles.append(
                        RoleRecord(
                            role_number=role_num_str,
                            title=title if title else role_num_str,
                            old_regulation=old_reg,
                            division=division,
                            sub_division=sub_division,
                            group=group,
                            family=family,
                            description=desc,
                        )
                    )
                    chunks.extend(self.chunker.chunk_role(role_num_str, desc))

        return roles, chunks

    async def index_data(self, raw_data: Any, batch_size: int = 64) -> dict[str, int]:
        roles, chunks = self.parse_raw_data(raw_data)
        logger.info("Parsed input roles=%d chunks=%d", len(roles), len(chunks))
        if not roles:
            logger.warning("No valid roles found in input; skipping indexing")
            return {"indexed_roles": 0, "indexed_chunks": 0}

        await self.role_repo.upsert_roles(roles)

        all_dense: list[list[float]] = []
        all_sparse: list[SparseEmbedding] = []

        for i in range(0, len(chunks), batch_size):
            batch_texts = [c.text for c in chunks[i : i + batch_size]]
            dense_batch = self.embedding_service.embed_dense_documents(batch_texts)
            sparse_batch = self.embedding_service.embed_sparse_documents(batch_texts)
            all_dense.extend(dense_batch)
            all_sparse.extend(sparse_batch)
            logger.debug(
                "Embedded chunk batch start=%d size=%d",
                i,
                len(batch_texts),
            )

        self.vector_repo.upsert_chunks(
            chunks=chunks,
            dense_embeddings=all_dense,
            sparse_embeddings=all_sparse,
            batch_size=batch_size,
        )

        stats = {
            "indexed_roles": len(roles),
            "indexed_chunks": len(chunks),
        }
        logger.info(
            "Indexing completed indexed_roles=%d indexed_chunks=%d",
            stats["indexed_roles"],
            stats["indexed_chunks"],
        )
        return stats

    async def index_from_file(self, file_path: str, batch_size: int = 64) -> dict[str, int]:
        logger.info("Loading indexing source path=%s", file_path)
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
        return await self.index_data(data, batch_size=batch_size)
