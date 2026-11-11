from typing import Annotated

from fastapi import APIRouter, Path, Query, status

from app.api.deps import RequestServiceDep
from app.domain.status import StatusCode
from app.schemas.request import (
    RequestCreate,
    RequestOut,
    RequestPage,
    RequestUpdate,
)

router = APIRouter()


@router.post("", response_model=RequestOut, status_code=status.HTTP_201_CREATED)
def create_request(
    payload: RequestCreate,
    service: RequestServiceDep,
) -> RequestOut:
    """Crea una solicitud en estado `created`.

    El estado no se acepta en el body: lo decide el servidor.
    """
    return RequestOut.model_validate(service.create(payload))


@router.get("", response_model=RequestPage)
def list_requests(
    service: RequestServiceDep,
    status_filter: StatusCode | None = Query(
        default=None,
        alias="status",
        description="Filtra por código de estado.",
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> RequestPage:
    items, total = service.list(
        status=status_filter,
        page=page,
        page_size=page_size,
    )
    return RequestPage(
        items=[RequestOut.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{request_id}", response_model=RequestOut)
def get_request(
    service: RequestServiceDep,
    request_id: Annotated[int, Path(ge=1)],
) -> RequestOut:
    return RequestOut.model_validate(service.get(request_id))


@router.patch("/{request_id}", response_model=RequestOut)
def update_request(
    payload: RequestUpdate,
    service: RequestServiceDep,
    request_id: Annotated[int, Path(ge=1)],
) -> RequestOut:
    """Edita título y/o descripción. No permite cambiar el estado."""
    return RequestOut.model_validate(service.update(request_id, payload))
