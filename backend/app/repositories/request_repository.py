from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.domain.status import StatusCode
from app.models.request import Request
from app.models.status import Status


class RequestRepository:
    """Todo el acceso a datos de solicitudes queda encapsulado aquí."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        *,
        title: str,
        description: str | None,
        status: Status,
    ) -> Request:
        request = Request(title=title, description=description, status=status)
        self.db.add(request)
        self.db.flush()
        return request

    def get_by_id(self, request_id: int) -> Request | None:
        return self.db.get(Request, request_id)

    def list_paginated(
        self,
        *,
        status: StatusCode | None,
        page: int,
        page_size: int,
    ) -> tuple[Sequence[Request], int]:
        filters = []
        if status is not None:
            filters.append(Request.status.has(Status.code == status.value))

        total = (
            self.db.scalar(select(func.count()).select_from(Request).where(*filters))
            or 0
        )

        stmt = (
            select(Request)
            .where(*filters)
            .order_by(Request.created_at.desc(), Request.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = self.db.scalars(stmt).all()
        return items, total

    def update_status(self, request: Request, status: Status) -> Request:
        request.status = status
        request.status_id = status.id
        self.db.flush()
        return request
