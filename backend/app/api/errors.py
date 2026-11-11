import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.domain.errors import (
    DomainError,
    InvalidTransitionError,
    RequestNotFoundError,
    UnknownStatusError,
)

logger = logging.getLogger(__name__)


def _http_status(exc: DomainError) -> int:
    if isinstance(exc, RequestNotFoundError):
        return 404
    if isinstance(exc, InvalidTransitionError):
        return 409
    if isinstance(exc, UnknownStatusError):
        return 422
    return 400


def _details(exc: DomainError) -> dict:
    if isinstance(exc, InvalidTransitionError):
        return {
            "from": str(exc.current),
            "to": str(exc.target),
            "allowed": [str(status) for status in exc.allowed],
        }
    if isinstance(exc, RequestNotFoundError):
        return {"request_id": exc.request_id}
    if isinstance(exc, UnknownStatusError):
        return {"status": exc.status}
    return {}


def _validation_details(exc: RequestValidationError) -> list[dict[str, str]]:
    details = []
    for error in exc.errors():
        field = ".".join(str(part) for part in error["loc"] if part != "body")
        details.append(
            {
                "field": field or "body",
                "message": error["msg"],
                "type": error["type"],
            }
        )
    return details


def error_response(
    *,
    status_code: int,
    code: str,
    message: str,
    details: dict | list | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
            }
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def domain_error_handler(_: Request, exc: DomainError) -> JSONResponse:
        return error_response(
            status_code=_http_status(exc),
            code=exc.code,
            message=exc.message,
            details=_details(exc),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        _: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return error_response(
            status_code=422,
            code="VALIDATION_ERROR",
            message="Datos de entrada inválidos.",
            details={"fields": _validation_details(exc)},
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Error no controlado", exc_info=exc)
        return error_response(
            status_code=500,
            code="INTERNAL_ERROR",
            message="Ocurrió un error inesperado. Intenta de nuevo más tarde.",
        )
