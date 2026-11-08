import pytest
from pydantic import ValidationError
from app.models.schemas import (
    HealthResponse,
    RoleDescriptionResponse,
    RoleDetailResponse,
    RoleQueryRequest,
    SearchRequest,
    SearchResponse,
    SearchResultItem,
)


def test_search_request_valid():
    req = SearchRequest(query="software engineer", top_k=5)
    assert req.query == "software engineer"
    assert req.top_k == 5


def test_search_request_defaults():
    req = SearchRequest(query="data")
    assert req.top_k == 10


def test_search_request_invalid_empty():
    with pytest.raises(ValidationError):
        SearchRequest(query="")


def test_search_request_invalid_top_k():
    with pytest.raises(ValidationError):
        SearchRequest(query="test", top_k=0)
    with pytest.raises(ValidationError):
        SearchRequest(query="test", top_k=1000)


def test_role_query_request_validation():
    req = RoleQueryRequest(role_number="1111.0100")
    assert req.role_number == "1111.0100"
    with pytest.raises(ValidationError):
        RoleQueryRequest(role_number="")


def test_search_response_serialization():
    item = SearchResultItem(
        rank=1,
        id="1111.0100_chunk0",
        role_number="1111.0100",
        role_title="Elected Official",
        chunk_index=0,
        chunk_text="Description snippet",
        score=0.88,
        combined_score=0.88,
        occupational_title="Elected Official",
        nco_2015="1111.0100",
        nco_2004="1111.10",
        division="Managers",
        sub_division="Chief Executives",
        group="Legislators",
        family="Legislators",
    )
    resp = SearchResponse(query="official", total=1, results=[item])
    data = resp.model_dump(by_alias=True)
    assert data["query"] == "official"
    assert data["total"] == 1
    first_res = data["results"][0]
    assert first_res["combined_score"] == 0.88
    assert first_res["rank"] == 1
    assert first_res["Occupational Title"] == "Elected Official"
    assert first_res["NCO 2015"] == "1111.0100"
    assert first_res["NCO 2004"] == "1111.10"
    assert first_res["Division"] == "Managers"
    assert first_res["Sub Division"] == "Chief Executives"
    assert first_res["Group"] == "Legislators"
    assert first_res["Family"] == "Legislators"


def test_health_response_model():
    h = HealthResponse(
        status="healthy",
        qdrant_status=True,
        version="2.0.0",
        vector_count=50,
        role_count=25,
    )
    assert h.status == "healthy"
    assert h.vector_count == 50
    assert h.role_count == 25
