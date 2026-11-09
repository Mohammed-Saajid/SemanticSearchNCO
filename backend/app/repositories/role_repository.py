import asyncio
import logging
from collections.abc import AsyncIterator, Iterable
from contextlib import asynccontextmanager

import aiosqlite

from app.models.domain import RoleRecord


logger = logging.getLogger(__name__)


class RoleRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._initialized: bool = False
        self._init_lock = asyncio.Lock()
        logger.info("Opening role repository path=%s", db_path)

    @asynccontextmanager
    async def _get_connection(self) -> AsyncIterator[aiosqlite.Connection]:
        async with aiosqlite.connect(self.db_path) as connection:
            connection.row_factory = aiosqlite.Row
            yield connection

    async def _ensure_initialized(self) -> None:
        async with self._init_lock:
            if self._initialized:
                return
            async with self._get_connection() as conn:
                await conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS roles (
                        role_number TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        old_regulation TEXT,
                        division TEXT DEFAULT '',
                        sub_division TEXT DEFAULT '',
                        group_name TEXT DEFAULT '',
                        family TEXT DEFAULT '',
                        description TEXT NOT NULL
                    )
                    """
                )
                cursor = await conn.execute("PRAGMA table_info(roles)")
                columns = {row[1] for row in await cursor.fetchall()}
                for column in ("division", "sub_division", "group_name", "family"):
                    if column not in columns:
                        await conn.execute(f"ALTER TABLE roles ADD COLUMN {column} TEXT DEFAULT ''")
                await conn.commit()
            self._initialized = True

    async def upsert_roles(self, roles: Iterable[RoleRecord]) -> int:
        records = [
            (
                role.role_number,
                role.title,
                role.old_regulation,
                role.division,
                role.sub_division,
                role.group,
                role.family,
                role.description,
            )
            for role in roles
        ]
        if not records:
            logger.debug("Skipping empty role upsert")
            return 0
        await self._ensure_initialized()
        async with self._get_connection() as conn:
            await conn.executemany(
                """
                INSERT INTO roles (
                    role_number, title, old_regulation, division, sub_division,
                    group_name, family, description
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(role_number) DO UPDATE SET
                    title=excluded.title,
                    old_regulation=excluded.old_regulation,
                    division=excluded.division,
                    sub_division=excluded.sub_division,
                    group_name=excluded.group_name,
                    family=excluded.family,
                    description=excluded.description
                """,
                records,
            )
            await conn.commit()
        logger.info("Role upsert completed roles=%d", len(records))
        return len(records)

    @staticmethod
    def _record_from_row(row: aiosqlite.Row) -> RoleRecord:
        return RoleRecord(
            role_number=row["role_number"],
            title=row["title"],
            old_regulation=row["old_regulation"] or "",
            division=row["division"] or "",
            sub_division=row["sub_division"] or "",
            group=row["group_name"] or "",
            family=row["family"] or "",
            description=row["description"],
        )

    async def get_by_role_number(self, role_number: str) -> RoleRecord | None:
        await self._ensure_initialized()
        async with self._get_connection() as conn:
            cursor = await conn.execute(
                """
                SELECT role_number, title, old_regulation, division, sub_division,
                       group_name, family, description
                FROM roles WHERE role_number = ?
                """,
                (role_number,),
            )
            row = await cursor.fetchone()
        if row is None:
            logger.debug("Role not found role_number=%s", role_number)
            return None
        return self._record_from_row(row)

    async def get_roles_batch(self, role_numbers: list[str]) -> dict[str, RoleRecord]:
        if not role_numbers:
            return {}
        await self._ensure_initialized()
        unique_numbers = list(dict.fromkeys(role_numbers))
        placeholders = ",".join("?" for _ in unique_numbers)
        async with self._get_connection() as conn:
            cursor = await conn.execute(
                f"""
                SELECT role_number, title, old_regulation, division, sub_division,
                       group_name, family, description
                FROM roles WHERE role_number IN ({placeholders})
                """,  # nosec B608 - placeholders are generated and values are bound below
                unique_numbers,
            )
            rows = await cursor.fetchall()
        roles = {row["role_number"]: self._record_from_row(row) for row in rows}
        logger.debug("Role batch lookup requested=%d found=%d", len(unique_numbers), len(roles))
        return roles

    async def get_titles_batch(self, role_numbers: list[str]) -> dict[str, str]:
        roles_map = await self.get_roles_batch(role_numbers)
        return {role_number: role.title for role_number, role in roles_map.items()}

    async def count(self) -> int:
        await self._ensure_initialized()
        async with self._get_connection() as conn:
            cursor = await conn.execute("SELECT COUNT(*) FROM roles")
            row = await cursor.fetchone()
        count = row[0] if row else 0
        logger.debug("Role count=%d", count)
        return count
