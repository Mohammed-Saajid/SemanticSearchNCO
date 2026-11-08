import logging

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
logger = logging.getLogger(__name__)


@router.post("/search", response_model=SearchResponse, tags=["Search"])
def search(
    request: SearchRequest,
    service: SearchService = Depends(get_search_service),
) -> SearchResponse:
    logger.debug("Search request received top_k=%d offset=%d", request.top_k, request.offset)
    return service.search(
        query=request.query,
        top_k=request.top_k,
        offset=request.offset,
    )


@router.get("/getroledescription", response_model=RoleDescriptionResponse, tags=["Roles"])
def get_role_description_get(
    role_number: str = Query(..., min_length=1),
    service: SearchService = Depends(get_search_service),
) -> RoleDescriptionResponse:
    logger.debug("Role description requested role_number=%s", role_number)
    return service.get_role_description(role_number=role_number)


@router.post("/getroledescription", response_model=RoleDescriptionResponse, tags=["Roles"])
def get_role_description_post(
    request: RoleQueryRequest,
    service: SearchService = Depends(get_search_service),
) -> RoleDescriptionResponse:
    logger.debug("Role description requested role_number=%s", request.role_number)
    return service.get_role_description(role_number=request.role_number)


@router.get("/roles/{role_number}", response_model=RoleDetailResponse, tags=["Roles"])
def get_role_detail(
    role_number: str,
    service: SearchService = Depends(get_search_service),
) -> RoleDetailResponse:
    detail = service.get_role_detail(role_number=role_number)
    if detail is None:
        logger.info("Role detail not found role_number=%s", role_number)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with number '{role_number}' not found",
        )
    logger.debug("Role detail returned role_number=%s", role_number)
    return detail
