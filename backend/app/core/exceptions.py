import logging
from typing import Any

from fastapi import Request, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class AppException(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class EntityNotFoundException(AppException):
    def __init__(self, entity_name: str, identifier: Any):
        super().__init__(
            message=f"{entity_name} with identifier '{identifier}' not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"entity": entity_name, "identifier": identifier},
        )


class IndexingException(AppException):
    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
        )


class SearchException(AppException):
    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
        )


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    logger.warning(
        "Application error method=%s path=%s status=%d error=%s",
        request.method,
        request.url.path,
        exc.status_code,
        exc.message,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "status_code": exc.status_code,
            "details": exc.details,
            "path": request.url.path,
        },
    )


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(
        "Unhandled application error method=%s path=%s",
        request.method,
        request.url.path,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "details": {"exception_type": type(exc).__name__, "message": str(exc)},
            "path": request.url.path,
        },
    )
