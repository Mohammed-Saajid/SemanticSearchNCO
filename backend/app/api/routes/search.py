from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.api.dependencies import get_search_service
from app.models.schemas import (
    RoleDescriptionResponse,
    RoleDetailResponse,
    RoleQueryRequest,
    SearchRequest,
    SearchResponse,
)
from app.services.search import SearchService

router = APIRouter()


@router.post("/search", response_model=SearchResponse, tags=["Search"])
@router.post("/api/v1/search", response_model=SearchResponse, tags=["Search"])
def search(
    request: SearchRequest,
    service: SearchService = Depends(get_search_service),
) -> SearchResponse:
    return service.search(
        query=request.query,
        top_k=request.top_k,
        offset=request.offset,
        bm25_weight=request.bm25_weight,
        vector_weight=request.vector_weight,
    )


@router.get("/getroledescription", response_model=RoleDescriptionResponse, tags=["Roles"])
def get_role_description_get(
    role_number: str = Query(..., min_length=1),
    service: SearchService = Depends(get_search_service),
) -> RoleDescriptionResponse:
    return service.get_role_description(role_number=role_number)


@router.post("/getroledescription", response_model=RoleDescriptionResponse, tags=["Roles"])
def get_role_description_post(
    request: RoleQueryRequest,
    service: SearchService = Depends(get_search_service),
) -> RoleDescriptionResponse:
    return service.get_role_description(role_number=request.role_number)


@router.get("/api/v1/roles/{role_number}", response_model=RoleDetailResponse, tags=["Roles"])
def get_role_detail(
    role_number: str,
    service: SearchService = Depends(get_search_service),
) -> RoleDetailResponse:
    detail = service.get_role_detail(role_number=role_number)
    if detail is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with number '{role_number}' not found",
        )
    return detail
