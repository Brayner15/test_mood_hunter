import logging
import time

import httpx

from app.integrations.llm.base import (
    LLMClient,
    LLMConfigurationError,
    LLMError,
    LLMTimeoutError,
)

logger = logging.getLogger(__name__)

# El prompt de sistema vive en el servicio; aquí solo se define el rol.
SYSTEM_MESSAGE = (
    "Eres un analista breve y preciso. Respondes en español y no inventas datos."
)


class OpenAILLMClient:
    """Cliente para la API de chat completions compatible con OpenAI.

    Funciona con OpenAI y con proveedores compatibles (Groq, DeepSeek, etc.)
    cambiando `LLM_BASE_URL` y `LLM_MODEL`.
    """

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        base_url: str,
        timeout_seconds: float,
        max_retries: int,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.max_retries = max(0, max_retries)

    async def summarize(self, prompt: str) -> str:
        if not self.api_key:
            raise LLMConfigurationError(
                "LLM_API_KEY no está configurada; no se puede generar el resumen."
            )

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_MESSAGE},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 350,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # El timeout es un presupuesto total compartido entre reintentos.
        deadline = time.monotonic() + self.timeout_seconds
        last_error: Exception | None = None

        for attempt in range(self.max_retries + 1):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break

            try:
                async with httpx.AsyncClient(timeout=remaining) as client:
                    response = await client.post(
                        f"{self.base_url}/chat/completions",
                        headers=headers,
                        json=payload,
                    )
                    response.raise_for_status()
                return self._extract_content(response.json())
            except httpx.TimeoutException as exc:
                last_error = exc
                logger.warning(
                    "Timeout del LLM (intento %s/%s)",
                    attempt + 1,
                    self.max_retries + 1,
                )
            except httpx.TransportError as exc:
                last_error = exc
                logger.warning("Error de red con el LLM: %s", exc)
            except httpx.HTTPStatusError as exc:
                last_error = exc
                code = exc.response.status_code
                logger.warning("El LLM respondió HTTP %s", code)
                # 4xx (salvo 429) no se arregla reintentando.
                if code != 429 and code < 500:
                    break
            except LLMError:
                raise
            except (KeyError, IndexError, TypeError, ValueError) as exc:
                last_error = exc
                break

        if isinstance(last_error, httpx.TimeoutException) or (
            last_error is None and time.monotonic() >= deadline
        ):
            raise LLMTimeoutError("El proveedor LLM no respondió a tiempo.")
        raise LLMError("No se pudo obtener el resumen del proveedor LLM.") from last_error

    @staticmethod
    def _extract_content(data: dict) -> str:
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMError("El LLM devolvió una respuesta con formato inesperado.") from exc

        if not isinstance(content, str):
            raise LLMError("El LLM devolvió una respuesta vacía o inválida.")
        return content.strip()
