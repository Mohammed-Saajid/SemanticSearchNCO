import logging
import sqlite3
from collections.abc import Iterable

from app.models.domain import RoleRecord


logger = logging.getLogger(__name__)


class RoleRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path
        logger.info("Opening role repository path=%s", db_path)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute(
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
            columns = [row[1] for row in conn.execute("PRAGMA table_info(roles)").fetchall()]
            for col in ["division", "sub_division", "group_name", "family"]:
                if col not in columns:
                    conn.execute(f"ALTER TABLE roles ADD COLUMN {col} TEXT DEFAULT ''")
            conn.commit()

    def upsert_roles(self, roles: Iterable[RoleRecord]) -> int:
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
        with self._get_connection() as conn:
            conn.executemany(
                """
                INSERT INTO roles (
                    role_number,
                    title,
                    old_regulation,
                    division,
                    sub_division,
                    group_name,
                    family,
                    description
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
            conn.commit()
            logger.info("Role upsert completed roles=%d", len(records))
            return len(records)

    def get_by_role_number(self, role_number: str) -> RoleRecord | None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT role_number, title, old_regulation, division, sub_division, group_name, family, description
                FROM roles WHERE role_number = ?
                """,
                (role_number,),
            )
            row = cursor.fetchone()
            if row is None:
                logger.debug("Role not found role_number=%s", role_number)
                return None
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

    def get_roles_batch(self, role_numbers: list[str]) -> dict[str, RoleRecord]:
        if not role_numbers:
            return {}
        unique_numbers = list(set(role_numbers))
        placeholders = ",".join("?" for _ in unique_numbers)
        # Only generated SQLite placeholders are interpolated; values remain bound parameters.
        query_template = """
            SELECT role_number, title, old_regulation, division, sub_division, group_name, family, description
            FROM roles WHERE role_number IN ({})
        """
        query = query_template.format(placeholders)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, unique_numbers)
            roles = {
                row["role_number"]: RoleRecord(
                    role_number=row["role_number"],
                    title=row["title"],
                    old_regulation=row["old_regulation"] or "",
                    division=row["division"] or "",
                    sub_division=row["sub_division"] or "",
                    group=row["group_name"] or "",
                    family=row["family"] or "",
                    description=row["description"],
                )
                for row in cursor.fetchall()
            }
            logger.debug(
                "Role batch lookup requested=%d found=%d",
                len(unique_numbers),
                len(roles),
            )
            return roles

    def get_titles_batch(self, role_numbers: list[str]) -> dict[str, str]:
        roles_map = self.get_roles_batch(role_numbers)
        return {k: v.title for k, v in roles_map.items()}

    def count(self) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM roles")
            row = cursor.fetchone()
            count = row[0] if row else 0
            logger.debug("Role count=%d", count)
            return count
