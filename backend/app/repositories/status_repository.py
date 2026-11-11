from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.status import StatusCode
from app.models.status import Status


class StatusRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_all(self) -> Sequence[Status]:
        return self.db.scalars(select(Status).order_by(Status.sort_order)).all()

    def get_by_code(self, code: StatusCode | str) -> Status | None:
        value = code.value if isinstance(code, StatusCode) else code
        return self.db.scalar(select(Status).where(Status.code == value))
