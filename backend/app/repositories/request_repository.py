from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session, contains_eager, lazyload

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

    def get_by_id_for_update(self, request_id: int) -> Request | None:
        """Lee la fila bloqueándola hasta el commit/rollback.

        Evita que dos transiciones concurrentes se pisen. En SQLite el
        `FOR UPDATE` se ignora; en MySQL bloquea la fila de `requests`.
        Se evita el eager join a `statuses` porque MySQL no permite
        `FOR UPDATE` sobre el lado nullable de un outer join.
        """
        stmt = (
            select(Request)
            .options(lazyload(Request.status))
            .where(Request.id == request_id)
            .with_for_update()
        )
        return self.db.scalar(stmt)

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

    def count_by_status(self) -> dict[str, int]:
        """Conteo por estado, incluyendo estados con cero solicitudes."""
        stmt = (
            select(Status.code, func.count(Request.id))
            .outerjoin(Request, Request.status_id == Status.id)
            .group_by(Status.id, Status.code, Status.sort_order)
            .order_by(Status.sort_order)
        )
        return {code: count for code, count in self.db.execute(stmt).all()}

    def list_paused(self, limit: int) -> Sequence[Request]:
        stmt = (
            select(Request)
            .join(Request.status)
            .options(contains_eager(Request.status))
            .where(Status.code == StatusCode.PAUSED.value)
            .order_by(Request.updated_at.asc(), Request.id.asc())
            .limit(limit)
        )
        return self.db.scalars(stmt).all()

    def list_oldest_open(self, limit: int) -> Sequence[Request]:
        """Solicitudes no finales que llevan más tiempo sin cambios (sin pausadas)."""
        stmt = (
            select(Request)
            .join(Request.status)
            .options(contains_eager(Request.status))
            .where(
                Status.is_final.is_(False),
                Status.code != StatusCode.PAUSED.value,
            )
            .order_by(Request.updated_at.asc(), Request.id.asc())
            .limit(limit)
        )
        return self.db.scalars(stmt).all()
