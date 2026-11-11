from sqlalchemy import Boolean, Integer, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Status(Base):
    """Catálogo de estados.

    `code` es el identificador que usa la API; `id` queda como detalle interno.
    """

    __tablename__ = "statuses"

    id: Mapped[int] = mapped_column(
        SmallInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    label: Mapped[str] = mapped_column(String(60), nullable=False)
    sort_order: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    is_final: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
