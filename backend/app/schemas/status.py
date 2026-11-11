from pydantic import BaseModel, ConfigDict

from app.domain.status import StatusCode


class StatusOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: StatusCode
    label: str
    is_final: bool
