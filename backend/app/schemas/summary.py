from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_serializer


class SummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: Literal["ok", "unavailable"]
    summary: str | None = None
    generated_at: datetime | None = None
    cached: bool = False
    message: str | None = None

    @field_serializer("generated_at", when_used="json")
    def serialize_generated_at(self, value: datetime | None) -> str | None:
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
