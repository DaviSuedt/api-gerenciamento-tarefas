import os
from pathlib import Path

os.environ["DATABASE_PATH"] = "test-data/test.db"
os.environ["API_KEY"] = "teste-seguro"

from fastapi.testclient import TestClient

from app.main import app, initialize_database


client = TestClient(app)
headers = {"X-API-Key": "teste-seguro"}


def setup_function() -> None:
    database = Path("test-data/test.db")
    if database.exists():
        database.unlink()
    initialize_database()


def test_crud_completo() -> None:
    created = client.post(
        "/tarefas",
        headers=headers,
        json={"titulo": "Preparar apresentação", "prioridade": "alta"},
    )
    assert created.status_code == 201
    task_id = created.json()["id"]

    listed = client.get("/tarefas", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    updated = client.patch(
        f"/tarefas/{task_id}", headers=headers, json={"concluida": True}
    )
    assert updated.status_code == 200
    assert updated.json()["concluida"] is True

    deleted = client.delete(f"/tarefas/{task_id}", headers=headers)
    assert deleted.status_code == 204
    assert client.get(f"/tarefas/{task_id}", headers=headers).status_code == 404


def test_bloqueia_requisicao_sem_chave() -> None:
    response = client.get("/tarefas")
    assert response.status_code == 401


def test_valida_dados_invalidos() -> None:
    response = client.post(
        "/tarefas",
        headers=headers,
        json={"titulo": "x", "prioridade": "urgente"},
    )
    assert response.status_code == 422


def test_entrada_sql_e_tratada_como_texto() -> None:
    malicious_title = "'); DROP TABLE tarefas; --"
    response = client.post(
        "/tarefas", headers=headers, json={"titulo": malicious_title}
    )
    assert response.status_code == 201
    assert response.json()["titulo"] == malicious_title
    assert client.get("/tarefas", headers=headers).status_code == 200
