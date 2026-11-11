from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.status import Status


def utcnow() -> datetime:
    """UTC naive: MySQL DATETIME no guarda zona horaria."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Request(Base):
    __tablename__ = "requests"

    # with_variant: SQLite solo autoincrementa claves declaradas como INTEGER.
    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status_id: Mapped[int] = mapped_column(
        SmallInteger,
        ForeignKey("statuses.id"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=utcnow, onupdate=utcnow
    )

    status: Mapped["Status"] = relationship(lazy="joined")
