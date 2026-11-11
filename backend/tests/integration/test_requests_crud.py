from fastapi.testclient import TestClient


def create_request(
    client: TestClient,
    *,
    title: str = "Solicitud de prueba",
    description: str | None = "Descripción inicial",
) -> dict:
    response = client.post(
        "/api/v1/requests",
        json={"title": title, "description": description},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_crear_solicitud_entra_en_created(client: TestClient) -> None:
    body = create_request(client, title="  Revisar contrato  ")

    assert body["title"] == "Revisar contrato"  # trim automático
    assert body["description"] == "Descripción inicial"
    assert body["status"]["code"] == "created"
    assert body["status"]["label"] == "Creada"
    assert body["created_at"].endswith("Z")
    assert body["updated_at"].endswith("Z")
    assert "status_id" not in body


def test_crear_solicitud_sin_descripcion(client: TestClient) -> None:
    response = client.post(
        "/api/v1/requests", json={"title": "Solicitud sin detalle"}
    )

    assert response.status_code == 201
    assert response.json()["description"] is None


def test_crear_rechaza_titulo_corto_con_formato_de_error(
    client: TestClient,
) -> None:
    response = client.post("/api/v1/requests", json={"title": "ab"})

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert error["details"]["fields"][0]["field"] == "title"


def test_crear_rechaza_campo_status(client: TestClient) -> None:
    response = client.post(
        "/api/v1/requests",
        json={"title": "Intento de saltar el flujo", "status": "done"},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_listar_pagina_y_filtra_por_codigo_de_estado(client: TestClient) -> None:
    for index in range(3):
        create_request(client, title=f"Solicitud {index}")

    page = client.get("/api/v1/requests", params={"page": 1, "page_size": 2})
    assert page.status_code == 200
    body = page.json()
    assert body["total"] == 3
    assert body["page"] == 1
    assert body["page_size"] == 2
    assert len(body["items"]) == 2

    filtered = client.get(
        "/api/v1/requests", params={"status": "created", "page_size": 100}
    )
    assert filtered.status_code == 200
    assert filtered.json()["total"] == 3
    assert all(item["status"]["code"] == "created" for item in filtered.json()["items"])

    empty = client.get("/api/v1/requests", params={"status": "done"})
    assert empty.json()["total"] == 0


def test_listar_rechaza_estado_desconocido(client: TestClient) -> None:
    response = client.get("/api/v1/requests", params={"status": "invented"})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_obtener_detalle(client: TestClient) -> None:
    created = create_request(client)

    response = client.get(f"/api/v1/requests/{created['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_obtener_solicitud_inexistente(client: TestClient) -> None:
    response = client.get("/api/v1/requests/9999")

    assert response.status_code == 404
    error = response.json()["error"]
    assert error["code"] == "REQUEST_NOT_FOUND"
    assert error["details"]["request_id"] == 9999


def test_patch_edita_titulo_y_descripcion(client: TestClient) -> None:
    created = create_request(client)

    response = client.patch(
        f"/api/v1/requests/{created['id']}",
        json={"title": "Título actualizado", "description": "Nueva descripción"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Título actualizado"
    assert body["description"] == "Nueva descripción"
    assert body["status"]["code"] == "created"


def test_patch_permite_borrar_descripcion(client: TestClient) -> None:
    created = create_request(client)

    response = client.patch(
        f"/api/v1/requests/{created['id']}", json={"description": None}
    )

    assert response.status_code == 200
    assert response.json()["description"] is None


def test_patch_no_permite_cambiar_estado_y_no_modifica_la_bd(
    client: TestClient,
) -> None:
    created = create_request(client, title="No debe cambiar")

    response = client.patch(
        f"/api/v1/requests/{created['id']}",
        json={"title": "Título que no debe guardarse", "status": "done"},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"

    unchanged = client.get(f"/api/v1/requests/{created['id']}").json()
    assert unchanged["title"] == "No debe cambiar"
    assert unchanged["status"]["code"] == "created"


def test_patch_rechaza_body_vacio(client: TestClient) -> None:
    created = create_request(client)

    response = client.patch(f"/api/v1/requests/{created['id']}", json={})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_patch_rechaza_titulo_null(client: TestClient) -> None:
    created = create_request(client)

    response = client.patch(
        f"/api/v1/requests/{created['id']}", json={"title": None}
    )

    assert response.status_code == 422


def test_patch_solicitud_inexistente(client: TestClient) -> None:
    response = client.patch("/api/v1/requests/9999", json={"title": "No existe"})

    assert response.status_code == 404
