from app.models.domain import RoleChunk, RoleRecord, SparseEmbedding
from app.repositories.role_repository import RoleRepository
from app.repositories.vector_repository import VectorRepository
from app.services.search import SearchService


def test_search_empty_query(search_service: SearchService):
    resp = search_service.search("")
    assert resp.total == 0
    assert resp.results == []


def test_search_deduplication_and_enrichment(
    search_service: SearchService,
    vector_repository: VectorRepository,
    role_repository: RoleRepository,
    sample_roles: list[RoleRecord],
):
    role_repository.upsert_roles(sample_roles)

    chunks = [
        RoleChunk("1001.0100_c0", "1001.0100", 0, "software architecture patterns"),
        RoleChunk("1001.0100_c1", "1001.0100", 1, "software detailed components"),
        RoleChunk("1001.0200_c0", "1001.0200", 0, "data science machine learning models"),
    ]
    dense_embeddings = [
        [0.8, 0.2, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.9, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.1, 0.9, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    ]
    sparse_embeddings = [
        SparseEmbedding(indices=[1, 2], values=[1.0, 2.0]),
        SparseEmbedding(indices=[1, 3], values=[2.0, 1.0]),
        SparseEmbedding(indices=[5, 6], values=[1.5, 2.5]),
    ]
    vector_repository.upsert_chunks(chunks, dense_embeddings, sparse_embeddings)

    response = search_service.search("software architecture", top_k=5)
    role_numbers = [item.role_number for item in response.results]
    assert len(role_numbers) == len(set(role_numbers))
    assert response.total <= 2

    first_item = response.results[0]
    assert [item.rank for item in response.results] == list(range(1, len(response.results) + 1))
    assert first_item.role_title in ["Software Architect", "Data Scientist"]

    paged_response = search_service.search("software architecture", top_k=1, offset=1)
    assert len(paged_response.results) == 1
    assert paged_response.results[0].rank == 2


def test_get_role_description_found(
    search_service: SearchService,
    role_repository: RoleRepository,
    sample_roles: list[RoleRecord],
):
    role_repository.upsert_roles(sample_roles)
    resp = search_service.get_role_description("1001.0100")
    assert resp.role_number == "1001.0100"
    assert "software systems architecture" in resp.description
    assert resp.title == "Software Architect"


def test_get_role_description_not_found(search_service: SearchService):
    resp = search_service.get_role_description("non_existing")
    assert resp.description == "Role not found"
    assert resp.title is None


def test_get_role_detail(
    search_service: SearchService,
    role_repository: RoleRepository,
    sample_roles: list[RoleRecord],
):
    role_repository.upsert_roles(sample_roles)
    detail = search_service.get_role_detail("1001.0200")
    assert detail is not None
    assert detail.role_number == "1001.0200"
    assert detail.title == "Data Scientist"

    missing = search_service.get_role_detail("missing")
    assert missing is None
