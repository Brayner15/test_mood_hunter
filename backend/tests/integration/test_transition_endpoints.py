from fastapi.testclient import TestClient


def create_request(client: TestClient, title: str = "Solicitud de prueba") -> dict:
    response = client.post("/api/v1/requests", json={"title": title})
    assert response.status_code == 201, response.text
    return response.json()


def move(client: TestClient, request_id: int, to: str):
    return client.post(
        f"/api/v1/requests/{request_id}/transitions",
        json={"to": to},
    )


def advance_to(client: TestClient, request_id: int, *statuses: str) -> None:
    for target in statuses:
        response = move(client, request_id, target)
        assert response.status_code == 200, response.text


def current_status(client: TestClient, request_id: int) -> str:
    return client.get(f"/api/v1/requests/{request_id}").json()["status"]["code"]


def test_transiciones_disponibles_desde_created(client: TestClient) -> None:
    request = create_request(client)

    response = client.get(f"/api/v1/requests/{request['id']}/transitions")

    assert response.status_code == 200
    body = response.json()
    assert body["current"]["code"] == "created"
    assert [status["code"] for status in body["allowed"]] == ["in_review"]
    assert all("id" not in status for status in body["allowed"])


def test_transicion_valida_created_a_in_review(client: TestClient) -> None:
    request = create_request(client)

    response = move(client, request["id"], "in_review")

    assert response.status_code == 200
    body = response.json()
    assert body["status"]["code"] == "in_review"
    assert body["status"]["label"] == "En revisión"
    assert body["created_at"].endswith("Z")
    assert body["updated_at"].endswith("Z")


def test_created_a_in_progress_se_rechaza_y_no_modifica_la_bd(
    client: TestClient,
) -> None:
    request = create_request(client)

    response = move(client, request["id"], "in_progress")

    assert response.status_code == 409
    error = response.json()["error"]
    assert error["code"] == "INVALID_TRANSITION"
    assert error["details"] == {
        "from": "created",
        "to": "in_progress",
        "allowed": ["in_review"],
    }
    assert "created" in error["message"]
    assert "in_progress" in error["message"]

    assert current_status(client, request["id"]) == "created"


def test_paused_no_se_alcanza_desde_created(client: TestClient) -> None:
    request = create_request(client)

    response = move(client, request["id"], "paused")

    assert response.status_code == 409
    assert current_status(client, request["id"]) == "created"


def test_flujo_de_pausa_completo(client: TestClient) -> None:
    request = create_request(client)
    advance_to(client, request["id"], "in_review", "paused")

    options = client.get(f"/api/v1/requests/{request['id']}/transitions").json()
    assert options["current"]["code"] == "paused"
    assert [status["code"] for status in options["allowed"]] == [
        "in_review",
        "in_progress",
    ]

    # No se puede finalizar sin reanudar.
    rejected = move(client, request["id"], "done")
    assert rejected.status_code == 409
    assert rejected.json()["error"]["details"]["allowed"] == [
        "in_review",
        "in_progress",
    ]
    assert current_status(client, request["id"]) == "paused"

    # Reanudar a in_progress y terminar.
    resumed = move(client, request["id"], "in_progress")
    assert resumed.status_code == 200
    assert resumed.json()["status"]["code"] == "in_progress"

    finished = move(client, request["id"], "done")
    assert finished.status_code == 200
    assert finished.json()["status"]["code"] == "done"


def test_desde_paused_se_puede_volver_a_in_review(client: TestClient) -> None:
    request = create_request(client)
    advance_to(client, request["id"], "in_review", "in_progress", "paused")

    response = move(client, request["id"], "in_review")

    assert response.status_code == 200
    assert response.json()["status"]["code"] == "in_review"


def test_pausar_desde_in_progress(client: TestClient) -> None:
    request = create_request(client)
    advance_to(client, request["id"], "in_review", "in_progress")

    response = move(client, request["id"], "paused")

    assert response.status_code == 200
    assert response.json()["status"]["code"] == "paused"


def test_done_es_final(client: TestClient) -> None:
    request = create_request(client)
    advance_to(client, request["id"], "in_review", "in_progress", "done")

    options = client.get(f"/api/v1/requests/{request['id']}/transitions")
    assert options.json()["allowed"] == []

    for target in ["created", "in_review", "in_progress", "paused", "done"]:
        response = move(client, request["id"], target)
        assert response.status_code == 409

    assert current_status(client, request["id"]) == "done"


def test_transicion_al_mismo_estado_se_rechaza(client: TestClient) -> None:
    request = create_request(client)
    advance_to(client, request["id"], "in_review")

    response = move(client, request["id"], "in_review")

    assert response.status_code == 409
    assert current_status(client, request["id"]) == "in_review"


def test_destino_desconocido_devuelve_422(client: TestClient) -> None:
    request = create_request(client)

    response = move(client, request["id"], "invented")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_transicion_sobre_solicitud_inexistente(client: TestClient) -> None:
    response = move(client, 9999, "in_review")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "REQUEST_NOT_FOUND"


def test_opciones_de_solicitud_inexistente(client: TestClient) -> None:
    response = client.get("/api/v1/requests/9999/transitions")

    assert response.status_code == 404
