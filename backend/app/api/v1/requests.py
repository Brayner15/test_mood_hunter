from typing import Annotated

from fastapi import APIRouter, Path, Query, status

from app.api.deps import RequestServiceDep, SummaryServiceDep
from app.domain.status import StatusCode
from app.schemas.request import (
    RequestCreate,
    RequestOut,
    RequestPage,
    RequestUpdate,
)
from app.schemas.summary import SummaryOut
from app.schemas.transition import TransitionOptions, TransitionRequest

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


@router.get("/summary", response_model=SummaryOut)
async def summarize_requests(service: SummaryServiceDep) -> SummaryOut:
    """Resumen del tablero generado por el LLM.

    Endpoint independiente: si el proveedor falla, responde 200 con
    `status: unavailable` y el listado sigue funcionando con normalidad.
    """
    result = await service.generate()
    return SummaryOut.model_validate(result)


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


@router.get("/{request_id}/transitions", response_model=TransitionOptions)
def get_transitions(
    service: RequestServiceDep,
    request_id: Annotated[int, Path(ge=1)],
) -> TransitionOptions:
    """Transiciones que la UI puede ofrecer desde el estado actual."""
    request, allowed = service.get_transitions(request_id)
    return TransitionOptions(
        current=request.status,
        allowed=allowed,
    )


@router.post("/{request_id}/transitions", response_model=RequestOut)
def transition_request(
    payload: TransitionRequest,
    service: RequestServiceDep,
    request_id: Annotated[int, Path(ge=1)],
) -> RequestOut:
    """Ejecuta una transición. 409 si no está permitida desde el estado actual."""
    return RequestOut.model_validate(service.transition(request_id, payload))
