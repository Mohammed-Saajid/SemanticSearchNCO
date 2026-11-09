import pytest
from fastapi.testclient import TestClient

from app.models.domain import RoleRecord
from app.repositories.role_repository import RoleRepository
from app.services.indexer import IndexingService


@pytest.mark.asyncio
async def test_search_endpoint_success(
    test_client: TestClient,
    indexing_service: IndexingService,
    sample_roles: list[RoleRecord],
):
    await indexing_service.role_repo.upsert_roles(sample_roles)
    raw_data = [
        {
            "role_number": r.role_number,
            "Role Name": r.title,
            "2004 Regulation": r.old_regulation,
            "Division": r.division,
            "Sub Division": r.sub_division,
            "Group": r.group,
            "Family": r.family,
            "Role Description": r.description,
        }
        for r in sample_roles
    ]
    await indexing_service.index_data(raw_data)

    response = test_client.post("/search", json={"query": "software systems", "top_k": 3})
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "software systems"
    assert "results" in data
    assert len(data["results"]) >= 1

    first = data["results"][0]
    assert first["rank"] == 1
    assert "id" in first
    assert "role_number" in first
    assert "role_title" in first
    assert "chunk_text" in first
    assert "combined_score" in first

    assert "Occupational Title" in first
    assert "NCO 2015" in first
    assert "NCO 2004" in first
    assert "Division" in first
    assert "Sub Division" in first
    assert "Group" in first
    assert "Family" in first

    assert first["Occupational Title"] == first["role_title"]
    assert first["NCO 2015"] == first["role_number"]


def test_search_endpoint_validation_error(test_client: TestClient):
    response = test_client.post("/search", json={"query": ""})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_role_description_query_param(
    test_client: TestClient,
    role_repository: RoleRepository,
    sample_roles: list[RoleRecord],
):
    await role_repository.upsert_roles(sample_roles)
    response = test_client.get("/getroledescription?role_number=1001.0100")
    assert response.status_code == 200
    data = response.json()
    assert data["role_number"] == "1001.0100"
    assert data["title"] == "Software Architect"
    assert "software systems architecture" in data["description"]


@pytest.mark.asyncio
async def test_get_role_description_post_body(
    test_client: TestClient,
    role_repository: RoleRepository,
    sample_roles: list[RoleRecord],
):
    await role_repository.upsert_roles(sample_roles)
    response = test_client.post("/getroledescription", json={"role_number": "1001.0200"})
    assert response.status_code == 200
    data = response.json()
    assert data["role_number"] == "1001.0200"
    assert data["title"] == "Data Scientist"


@pytest.mark.asyncio
async def test_get_role_detail_rest(
    test_client: TestClient,
    role_repository: RoleRepository,
    sample_roles: list[RoleRecord],
):
    await role_repository.upsert_roles(sample_roles)
    response = test_client.get("/roles/1001.0100")
    assert response.status_code == 200
    data = response.json()
    assert data["role_number"] == "1001.0100"
    assert data["title"] == "Software Architect"
    assert data["division"] == "Information Technology"
    assert data["sub_division"] == "Software Engineering"
    assert data["group"] == "Architecture"
    assert data["family"] == "Software Architecture"

    missing_resp = test_client.get("/roles/missing")
    assert missing_resp.status_code == 404
