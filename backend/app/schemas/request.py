from datetime import datetime, timezone

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
    field_serializer,
    model_validator,
)

from app.domain.status import StatusCode, status_sort_key
from app.domain.transitions import allowed_transitions
from app.schemas.status import StatusOut


class RequestCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str = Field(min_length=3, max_length=150)
    description: str | None = Field(default=None, max_length=5000)


class RequestUpdate(BaseModel):
    """PATCH parcial. El estado no es editable por esta vía."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str | None = Field(default=None, min_length=3, max_length=150)
    description: str | None = Field(default=None, max_length=5000)

    @model_validator(mode="after")
    def validate_changes(self) -> "RequestUpdate":
        if not self.model_fields_set:
            raise ValueError("Debes enviar al menos un campo: title o description.")
        if "title" in self.model_fields_set and self.title is None:
            raise ValueError("El título no puede ser null.")
        return self


class RequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    status: StatusOut
    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at", "updated_at", when_used="json")
    def serialize_datetime(self, value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def allowed_transitions(self) -> list[StatusCode]:
        """Destinos válidos desde el estado actual, calculados por el dominio.

        La UI solo ofrece estos botones; el backend vuelve a validar al ejecutar.
        """
        return sorted(
            allowed_transitions(StatusCode(self.status.code)),
            key=status_sort_key,
        )


class RequestPage(BaseModel):
    items: list[RequestOut]
    total: int
    page: int
    page_size: int
