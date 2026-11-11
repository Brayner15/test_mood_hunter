from collections.abc import Sequence

from sqlalchemy.orm import Session

from app.domain.errors import RequestNotFoundError, UnknownStatusError
from app.domain.status import StatusCode
from app.models.request import Request
from app.models.status import Status
from app.repositories.request_repository import RequestRepository
from app.repositories.status_repository import StatusRepository
from app.schemas.request import RequestCreate, RequestUpdate


class RequestService:
    """Casos de uso de solicitudes. Los routers no hablan con SQLAlchemy."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.requests = RequestRepository(db)
        self.statuses = StatusRepository(db)

    def create(self, payload: RequestCreate) -> Request:
        status = self.statuses.get_by_code(StatusCode.CREATED)
        if status is None:
            raise UnknownStatusError(StatusCode.CREATED)

        request = self.requests.create(
            title=payload.title,
            description=payload.description or None,
            status=status,
        )
        self.db.commit()
        self.db.refresh(request)
        return request

    def list(
        self,
        *,
        status: StatusCode | None,
        page: int,
        page_size: int,
    ) -> tuple[Sequence[Request], int]:
        return self.requests.list_paginated(
            status=status,
            page=page,
            page_size=page_size,
        )

    def get(self, request_id: int) -> Request:
        request = self.requests.get_by_id(request_id)
        if request is None:
            raise RequestNotFoundError(request_id)
        return request

    def update(self, request_id: int, payload: RequestUpdate) -> Request:
        request = self.get(request_id)
        changes = payload.model_dump(exclude_unset=True)

        if "title" in changes:
            request.title = changes["title"]
        if "description" in changes:
            request.description = changes["description"] or None

        self.db.commit()
        self.db.refresh(request)
        return request

    def list_statuses(self) -> Sequence[Status]:
        return self.statuses.list_all()
