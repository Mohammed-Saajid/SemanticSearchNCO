from fastapi import APIRouter, Depends
from app.api.dependencies import get_role_repository, get_settings, get_vector_repository, check_qdrant_connection
from app.core.config import Settings
from app.models.schemas import HealthResponse
from app.repositories.role_repository import RoleRepository
from app.repositories.vector_repository import VectorRepository

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
def health_check(
    settings: Settings = Depends(get_settings),
    vector_repo: VectorRepository = Depends(get_vector_repository),
    role_repo: RoleRepository = Depends(get_role_repository),
) -> HealthResponse:
    return HealthResponse(
        status="healthy",
        qdrant_status=check_qdrant_connection(),
        version=settings.app_version,
        vector_count=vector_repo.count(),
        role_count=role_repo.count(),
    )

