from typing import Protocol


class LLMError(Exception):
    """Fallo genérico al generar el resumen."""


class LLMTimeoutError(LLMError):
    """El proveedor no respondió dentro del presupuesto de tiempo."""


class LLMConfigurationError(LLMError):
    """Falta configuración (por ejemplo, la API key)."""


class LLMClient(Protocol):
    """Contrato mínimo que debe cumplir cualquier proveedor."""

    async def summarize(self, prompt: str) -> str: ...
