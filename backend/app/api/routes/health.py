import logging

from fastapi import APIRouter, Depends

from app.api.dependencies import (
    check_qdrant_connection,
    get_role_repository,
    get_settings,
    get_vector_repository,
)
from app.core.config import Settings
from app.models.schemas import HealthResponse
from app.repositories.role_repository import RoleRepository
from app.repositories.vector_repository import VectorRepository

router = APIRouter(tags=["Health"])
logger = logging.getLogger(__name__)


@router.get("/health", response_model=HealthResponse)
def health_check(
    settings: Settings = Depends(get_settings),
    vector_repo: VectorRepository = Depends(get_vector_repository),
    role_repo: RoleRepository = Depends(get_role_repository),
) -> HealthResponse:
    qdrant_status = check_qdrant_connection()
    vector_count = vector_repo.count()
    role_count = role_repo.count()
    logger.info(
        "Health check status=%s qdrant_status=%s vector_count=%d role_count=%d",
        "healthy" if qdrant_status else "degraded",
        qdrant_status,
        vector_count,
        role_count,
    )
    return HealthResponse(
        status="healthy",
        qdrant_status=qdrant_status,
        version=settings.app_version,
        vector_count=vector_count,
        role_count=role_count,
    )
