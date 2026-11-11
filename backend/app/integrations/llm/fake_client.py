import json

from app.integrations.llm.base import LLMClient


class FakeLLMClient:
    """Proveedor de demostración: no hace llamadas externas ni gasta tokens.

    Se activa con `LLM_PROVIDER=fake` y permite probar la UI sin API key.
    """

    async def summarize(self, prompt: str) -> str:
        data = self._extract_payload(prompt)
        if data is None:
            return "Resumen simulado: no se pudieron interpretar los datos del tablero."

        total = data.get("total", 0)
        if not total:
            return "No hay solicitudes registradas en el tablero."

        by_status: dict[str, int] = data.get("por_estado", {})
        paused = data.get("pausadas", [])
        oldest = data.get("abiertas_mas_antiguas", [])

        parts = [f"Hay {total} solicitudes en el tablero."]
        if by_status:
            distribution = ", ".join(
                f"{status}: {count}" for status, count in by_status.items()
            )
            parts.append(f"Distribución por estado: {distribution}.")
        if paused:
            parts.append(
                f"Hay {len(paused)} solicitudes pausadas que conviene revisar."
            )
        if oldest:
            parts.append(
                "Las más antiguas sin avanzar son: "
                + ", ".join(item["titulo"] for item in oldest[:3])
                + "."
            )
        return " ".join(parts)

    @staticmethod
    def _extract_payload(prompt: str) -> dict | None:
        start = prompt.find("{")
        end = prompt.rfind("}")
        if start == -1 or end <= start:
            return None
        try:
            data = json.loads(prompt[start : end + 1])
        except json.JSONDecodeError:
            return None
        return data if isinstance(data, dict) else None
