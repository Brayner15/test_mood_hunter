from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.integrations.llm.base import LLMClient
from app.integrations.llm.factory import build_llm_client
from app.services.request_service import RequestService
from app.services.summary_service import SummaryService, get_summary_cache

SessionDep = Annotated[Session, Depends(get_db)]


def get_request_service(session: SessionDep) -> RequestService:
    return RequestService(session)


RequestServiceDep = Annotated[RequestService, Depends(get_request_service)]


def get_llm_client() -> LLMClient:
    return build_llm_client(settings)


LLMClientDep = Annotated[LLMClient, Depends(get_llm_client)]


def get_summary_service(
    session: SessionDep,
    llm: LLMClientDep,
) -> SummaryService:
    return SummaryService(session, llm, get_summary_cache())


SummaryServiceDep = Annotated[SummaryService, Depends(get_summary_service)]
