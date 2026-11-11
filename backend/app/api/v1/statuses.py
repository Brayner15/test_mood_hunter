from fastapi import APIRouter

from app.api.deps import RequestServiceDep
from app.schemas.status import StatusOut

router = APIRouter()


@router.get("", response_model=list[StatusOut])
def list_statuses(service: RequestServiceDep) -> list[StatusOut]:
    """Catálogo de estados. La API siempre usa `code`, nunca el id interno."""
    return [StatusOut.model_validate(status) for status in service.list_statuses()]
