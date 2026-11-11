from pydantic import BaseModel, ConfigDict

from app.domain.status import StatusCode
from app.schemas.status import StatusOut


class TransitionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    to: StatusCode


class TransitionOptions(BaseModel):
    current: StatusOut
    allowed: list[StatusOut]
