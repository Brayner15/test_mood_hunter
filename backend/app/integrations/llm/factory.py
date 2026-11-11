from app.core.config import Settings
from app.integrations.llm.base import LLMClient, LLMError
from app.integrations.llm.fake_client import FakeLLMClient
from app.integrations.llm.openai_client import OpenAILLMClient


class FailingLLMClient:
    """Cliente que siempre falla con un motivo explicable (config inválida)."""

    def __init__(self, reason: str) -> None:
        self.reason = reason

    async def summarize(self, prompt: str) -> str:
        raise LLMError(self.reason)


def build_llm_client(settings: Settings) -> LLMClient:
    provider = (settings.llm_provider or "").strip().lower()

    if provider == "fake":
        return FakeLLMClient()

    if provider == "openai":
        return OpenAILLMClient(
            api_key=settings.llm_api_key,
            model=settings.llm_model,
            base_url=settings.llm_base_url,
            timeout_seconds=settings.llm_timeout_seconds,
            max_retries=settings.llm_max_retries,
        )

    return FailingLLMClient(
        f"Proveedor LLM '{provider}' no soportado. Usa 'openai' o 'fake'."
    )
