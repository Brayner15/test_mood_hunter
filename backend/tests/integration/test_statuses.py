from fastapi.testclient import TestClient


def test_listar_catalogo_de_estados_por_codigo(client: TestClient) -> None:
    response = client.get("/api/v1/statuses")

    assert response.status_code == 200
    statuses = response.json()
    assert [status["code"] for status in statuses] == [
        "created",
        "in_review",
        "in_progress",
        "paused",
        "done",
    ]
    assert [status["label"] for status in statuses] == [
        "Creada",
        "En revisión",
        "En progreso",
        "Pausada",
        "Finalizada",
    ]
    assert statuses[-1]["is_final"] is True
    assert all("id" not in status for status in statuses)
