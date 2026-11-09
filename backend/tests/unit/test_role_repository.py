import pytest

from app.models.domain import RoleRecord
from app.repositories.role_repository import RoleRepository


@pytest.mark.asyncio
async def test_upsert_and_get_by_role_number(
    role_repository: RoleRepository,
    sample_roles: list[RoleRecord],
):
    assert await role_repository.count() == 0

    inserted = await role_repository.upsert_roles(sample_roles)
    assert inserted == 3
    assert await role_repository.count() == 3

    fetched = await role_repository.get_by_role_number("1001.0100")
    assert fetched is not None
    assert fetched.role_number == "1001.0100"
    assert fetched.title == "Software Architect"
    assert fetched.old_regulation == "1001.1"

    missing = await role_repository.get_by_role_number("9999.9999")
    assert missing is None


@pytest.mark.asyncio
async def test_upsert_overwrite(role_repository: RoleRepository):
    r1 = RoleRecord("1111.0100", "Initial Title", "old", "Initial description", "Div1", "Sub1", "Grp1", "Fam1")
    await role_repository.upsert_roles([r1])

    r2 = RoleRecord("1111.0100", "Updated Title", "new", "Updated description", "Div2", "Sub2", "Grp2", "Fam2")
    await role_repository.upsert_roles([r2])

    assert await role_repository.count() == 1
    fetched = await role_repository.get_by_role_number("1111.0100")
    assert fetched.title == "Updated Title"
    assert fetched.description == "Updated description"
    assert fetched.division == "Div2"
    assert fetched.family == "Fam2"


@pytest.mark.asyncio
async def test_get_titles_batch(
    role_repository: RoleRepository,
    sample_roles: list[RoleRecord],
):
    await role_repository.upsert_roles(sample_roles)

    titles = await role_repository.get_titles_batch(["1001.0100", "1001.0200", "missing.role"])
    assert len(titles) == 2
    assert titles["1001.0100"] == "Software Architect"
    assert titles["1001.0200"] == "Data Scientist"
    assert "missing.role" not in titles


@pytest.mark.asyncio
async def test_get_roles_batch(
    role_repository: RoleRepository,
    sample_roles: list[RoleRecord],
):
    await role_repository.upsert_roles(sample_roles)

    roles = await role_repository.get_roles_batch(["1001.0100", "missing.role"])
    assert len(roles) == 1
    assert roles["1001.0100"].title == "Software Architect"
    assert roles["1001.0100"].division == sample_roles[0].division


@pytest.mark.asyncio
async def test_get_titles_batch_empty(role_repository: RoleRepository):
    assert await role_repository.get_titles_batch([]) == {}
    assert await role_repository.get_roles_batch([]) == {}
