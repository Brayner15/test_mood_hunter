import asyncio

from fastapi.testclient import TestClient

from app.api.deps import get_llm_client
from app.integrations.llm.base import LLMError
from app.main import app


class StubLLM:
    """Cliente controlable para probar el endpoint sin llamar a un proveedor."""

    def __init__(
        self,
        response: str = "Hay solicitudes repartidas entre varios estados.",
        *,
        error: Exception | None = None,
        delay: float = 0.0,
    ) -> None:
        self.response = response
        self.error = error
        self.delay = delay
        self.calls = 0
        self.prompts: list[str] = []

    async def summarize(self, prompt: str) -> str:
        self.calls += 1
        self.prompts.append(prompt)
        if self.delay:
            await asyncio.sleep(self.delay)
        if self.error is not None:
            raise self.error
        return self.response


def use_llm(llm: StubLLM) -> None:
    app.dependency_overrides[get_llm_client] = lambda: llm


def create_request(
    client: TestClient,
    title: str = "Solicitud de prueba",
    description: str | None = "Descripción de prueba",
) -> dict:
    response = client.post(
        "/api/v1/requests",
        json={"title": title, "description": description},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_resumen_ok_y_segunda_llamada_desde_cache(client: TestClient) -> None:
    llm = StubLLM("Hay 2 solicitudes, ambas en created.")
    use_llm(llm)
    create_request(client, title="Primera")
    create_request(client, title="Segunda")

    response = client.get("/api/v1/requests/summary")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["summary"] == "Hay 2 solicitudes, ambas en created."
    assert body["cached"] is False
    assert body["message"] is None
    assert body["generated_at"].endswith("Z")
    assert llm.calls == 1

    again = client.get("/api/v1/requests/summary")

    assert again.status_code == 200
    assert again.json()["cached"] is True
    assert again.json()["summary"] == body["summary"]
    assert llm.calls == 1


def test_cache_se_invalida_cuando_cambian_los_datos(client: TestClient) -> None:
    llm = StubLLM()
    use_llm(llm)
    create_request(client, title="Primera")
    client.get("/api/v1/requests/summary")

    create_request(client, title="Segunda")
    client.get("/api/v1/requests/summary")

    assert llm.calls == 2


def test_fallo_del_llm_no_rompe_el_listado(client: TestClient) -> None:
    use_llm(StubLLM(error=LLMError("proveedor caído")))
    create_request(client)

    response = client.get("/api/v1/requests/summary")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "unavailable"
    assert body["summary"] is None
    assert "No pudimos generar el resumen" in body["message"]

    listing = client.get("/api/v1/requests")
    assert listing.status_code == 200
    assert listing.json()["total"] == 1


def test_respuesta_vacia_del_llm_se_trata_como_fallo(client: TestClient) -> None:
    use_llm(StubLLM(response="   "))
    create_request(client)

    response = client.get("/api/v1/requests/summary")

    assert response.status_code == 200
    assert response.json()["status"] == "unavailable"


def test_prompt_no_envia_descripciones_ni_ids(client: TestClient) -> None:
    llm = StubLLM()
    use_llm(llm)
    description = "SECRETO_NO_DEBE_VIAJAR_AL_MODELO"
    create_request(
        client,
        title="Solicitud con datos visibles",
        description=description,
    )

    client.get("/api/v1/requests/summary")

    prompt = llm.prompts[0]
    assert description not in prompt
    assert "Solicitud con datos visibles" in prompt
    assert '"description"' not in prompt
    assert '"id"' not in prompt


def test_titulos_largos_se_truncan_en_el_prompt(client: TestClient) -> None:
    llm = StubLLM()
    use_llm(llm)
    long_title = "T" * 140 + "ZZZ"
    create_request(client, title=long_title)

    client.get("/api/v1/requests/summary")

    prompt = llm.prompts[0]
    assert "ZZZ" not in prompt
    assert "T" * 81 not in prompt
    assert "T" * 80 in prompt
