import asyncio
import json

from sqlalchemy import select

from app.integrations.llm.fake_client import FakeLLMClient
from app.models.request import Request
from app.models.status import Status
from app.services.summary_service import SummaryCache, SummaryService


class SlowLLM:
    async def summarize(self, prompt: str) -> str:
        await asyncio.sleep(1)
        return "respuesta tardía"


class StubLLM:
    async def summarize(self, prompt: str) -> str:
        return "resumen"


def test_timeout_del_llm_devuelve_unavailable(session_factory) -> None:
    with session_factory() as session:
        service = SummaryService(
            session,
            SlowLLM(),
            SummaryCache(ttl_seconds=0),
            timeout_seconds=0.01,
        )
        result = asyncio.run(service.generate())

    assert result.status == "unavailable"
    assert result.summary is None
    assert result.message is not None


def test_payload_no_incluye_descripciones(session_factory) -> None:
    with session_factory() as session:
        status = session.scalar(select(Status).where(Status.code == "created"))
        session.add(
            Request(
                title="Título visible",
                description="SECRETO_EN_LA_DESCRIPCION",
                status=status,
            )
        )
        session.commit()

        service = SummaryService(session, StubLLM(), SummaryCache(ttl_seconds=0))
        payload = service.build_payload()

    serialized = json.dumps(payload)
    assert payload["total"] == 1
    assert payload["por_estado"]["created"] == 1
    assert "SECRETO_EN_LA_DESCRIPCION" not in serialized
    assert payload["abiertas_mas_antiguas"][0]["titulo"] == "Título visible"


def test_fake_client_genera_un_resumen_legible() -> None:
    prompt = (
        "Datos del tablero:\n"
        '{"total":2,"por_estado":{"created":2},"pausadas":[],'
        '"abiertas_mas_antiguas":[]}'
    )

    summary = asyncio.run(FakeLLMClient().summarize(prompt))

    assert "2 solicitudes" in summary
    assert "created: 2" in summary
