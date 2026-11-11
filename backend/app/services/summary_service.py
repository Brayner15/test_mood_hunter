import asyncio
import hashlib
import json
import logging
import threading
import time
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from sqlalchemy.orm import Session

from app.core.config import settings
from app.integrations.llm.base import LLMClient
from app.models.request import Request, utcnow
from app.repositories.request_repository import RequestRepository

logger = logging.getLogger(__name__)

MAX_ITEMS = 5
MAX_TITLE_LENGTH = 80

INSTRUCTIONS = """Resume el estado del tablero de solicitudes en español, en un máximo de 5 líneas y en texto plano.
Usa SOLO los datos JSON que se incluyen; no inventes cifras, solicitudes ni causas.
Destaca el total, dónde se acumulan las solicitudes y cuáles llevan más tiempo detenidas.
Estados: created=creada, in_review=en revisión, in_progress=en progreso, paused=pausada, done=finalizada.
No incluyas listas largas ni repitas los datos literalmente."""

UNAVAILABLE_MESSAGE = (
    "No pudimos generar el resumen en este momento. "
    "Intenta de nuevo en unos minutos."
)


@dataclass(frozen=True)
class SummaryResult:
    status: Literal["ok", "unavailable"]
    summary: str | None
    generated_at: datetime | None
    cached: bool
    message: str | None = None


@dataclass(frozen=True)
class CacheEntry:
    summary: str
    generated_at: datetime
    expires_at: float


class SummaryCache:
    """Cache en memoria con TTL, keyed por hash de los datos enviados al LLM."""

    def __init__(self, ttl_seconds: int) -> None:
        self.ttl_seconds = max(0, ttl_seconds)
        self._entries: dict[str, CacheEntry] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> CacheEntry | None:
        if self.ttl_seconds <= 0:
            return None
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                return None
            if entry.expires_at <= time.monotonic():
                self._entries.pop(key, None)
                return None
            return entry

    def set(self, key: str, summary: str) -> CacheEntry:
        entry = CacheEntry(
            summary=summary,
            generated_at=utcnow(),
            expires_at=time.monotonic() + self.ttl_seconds,
        )
        if self.ttl_seconds > 0:
            with self._lock:
                self._entries[key] = entry
        return entry

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()


_summary_cache = SummaryCache(settings.llm_cache_ttl_seconds)


def get_summary_cache() -> SummaryCache:
    return _summary_cache


def _truncate(text: str, limit: int = MAX_TITLE_LENGTH) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[:limit].rstrip() + "…"


def _days_since(value: datetime, now: datetime) -> int:
    return max((now - value).days, 0)


class SummaryService:
    """Genera un resumen del tablero minimizando los datos enviados al LLM.

    El listado nunca depende de este servicio: si el proveedor falla o tarda,
    se devuelve un resultado `unavailable` con un mensaje claro.
    """

    def __init__(
        self,
        db: Session,
        llm: LLMClient,
        cache: SummaryCache,
        *,
        timeout_seconds: float | None = None,
    ) -> None:
        self.db = db
        self.llm = llm
        self.cache = cache
        self.timeout_seconds = (
            timeout_seconds
            if timeout_seconds is not None
            else settings.llm_timeout_seconds
        )

    async def generate(self) -> SummaryResult:
        payload = self.build_payload()
        serialized = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        cache_key = hashlib.sha256(serialized.encode("utf-8")).hexdigest()

        cached = self.cache.get(cache_key)
        if cached is not None:
            return SummaryResult(
                status="ok",
                summary=cached.summary,
                generated_at=cached.generated_at,
                cached=True,
            )

        prompt = f"{INSTRUCTIONS}\n\nDatos del tablero:\n{serialized}"
        try:
            summary = await asyncio.wait_for(
                self.llm.summarize(prompt),
                # Margen sobre el timeout del cliente HTTP como red de seguridad.
                timeout=self.timeout_seconds + 0.5,
            )
        except Exception as exc:  # noqa: BLE001 - el resumen nunca debe romper el listado
            logger.warning("Resumen LLM no disponible: %s", exc)
            return SummaryResult(
                status="unavailable",
                summary=None,
                generated_at=None,
                cached=False,
                message=UNAVAILABLE_MESSAGE,
            )

        cleaned = (summary or "").strip()
        if not cleaned:
            logger.warning("El LLM devolvió un resumen vacío.")
            return SummaryResult(
                status="unavailable",
                summary=None,
                generated_at=None,
                cached=False,
                message=UNAVAILABLE_MESSAGE,
            )

        entry = self.cache.set(cache_key, cleaned)
        return SummaryResult(
            status="ok",
            summary=cleaned,
            generated_at=entry.generated_at,
            cached=False,
        )

    def build_payload(self) -> dict:
        """Datos mínimos para el resumen: agregados y títulos cortos, sin descripciones."""
        repository = RequestRepository(self.db)
        by_status = repository.count_by_status()
        now = utcnow()

        paused = self._items(
            repository.list_paused(MAX_ITEMS),
            now,
            include_status=False,
        )
        oldest_open = self._items(
            repository.list_oldest_open(MAX_ITEMS),
            now,
            include_status=True,
        )

        return {
            "total": sum(by_status.values()),
            "por_estado": by_status,
            "pausadas": paused,
            "abiertas_mas_antiguas": oldest_open,
        }

    @staticmethod
    def _items(
        requests: Sequence[Request],
        now: datetime,
        *,
        include_status: bool,
    ) -> list[dict]:
        items = []
        for request in requests:
            item = {
                "titulo": _truncate(request.title),
                "dias_sin_cambios": _days_since(request.updated_at, now),
            }
            if include_status:
                item["estado"] = request.status.code
            items.append(item)
        return items
