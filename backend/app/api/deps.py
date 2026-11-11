from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.request_service import RequestService

SessionDep = Annotated[Session, Depends(get_db)]


def get_request_service(session: SessionDep) -> RequestService:
    return RequestService(session)


RequestServiceDep = Annotated[RequestService, Depends(get_request_service)]
