import os
import sqlite3
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Response, status
from pydantic import BaseModel, ConfigDict, Field


DATABASE_PATH = Path(os.getenv("DATABASE_PATH", "data/tarefas.db"))
API_KEY = os.getenv("API_KEY", "chave-local-dev")

class TaskCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    titulo: str = Field(min_length=3, max_length=120)
    descricao: str = Field(default="", max_length=500)
    prioridade: Literal["baixa", "media", "alta"] = "media"


class TaskUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    titulo: str | None = Field(default=None, min_length=3, max_length=120)
    descricao: str | None = Field(default=None, max_length=500)
    prioridade: Literal["baixa", "media", "alta"] | None = None
    concluida: bool | None = None


class Task(BaseModel):
    id: int
    titulo: str
    descricao: str
    prioridade: str
    concluida: bool
    criada_em: str
    atualizada_em: str


@contextmanager
def database() -> Iterator[sqlite3.Connection]:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def initialize_database() -> None:
    with database() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS tarefas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL CHECK(length(titulo) BETWEEN 3 AND 120),
                descricao TEXT NOT NULL DEFAULT '',
                prioridade TEXT NOT NULL DEFAULT 'media'
                    CHECK(prioridade IN ('baixa', 'media', 'alta')),
                concluida INTEGER NOT NULL DEFAULT 0 CHECK(concluida IN (0, 1)),
                criada_em TEXT NOT NULL,
                atualizada_em TEXT NOT NULL
            )
            """
        )


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="API de Gerenciamento de Tarefas",
    description="API REST com SQLite desenvolvida para a GS de Cloud Security Prevention e DevSecOps.",
    version="1.0.0",
    lifespan=lifespan,
)


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    if not x_api_key or x_api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Chave de API ausente ou inválida.",
        )


def task_from_row(row: sqlite3.Row) -> Task:
    return Task(
        id=row["id"],
        titulo=row["titulo"],
        descricao=row["descricao"],
        prioridade=row["prioridade"],
        concluida=bool(row["concluida"]),
        criada_em=row["criada_em"],
        atualizada_em=row["atualizada_em"],
    )


@app.get("/", tags=["Informações"])
def root() -> dict[str, str]:
    return {
        "aplicacao": "API de Gerenciamento de Tarefas",
        "documentacao": "/docs",
        "saude": "/health",
    }


@app.get("/health", tags=["Informações"])
def health() -> dict[str, str]:
    with database() as connection:
        connection.execute("SELECT 1").fetchone()
    return {"status": "ok", "banco": "conectado"}


@app.post(
    "/tarefas",
    response_model=Task,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_api_key)],
    tags=["Tarefas"],
)
def create_task(payload: TaskCreate) -> Task:
    now = datetime.now(timezone.utc).isoformat()
    with database() as connection:
        cursor = connection.execute(
            """
            INSERT INTO tarefas (titulo, descricao, prioridade, criada_em, atualizada_em)
            VALUES (?, ?, ?, ?, ?)
            """,
            (payload.titulo, payload.descricao, payload.prioridade, now, now),
        )
        row = connection.execute(
            "SELECT * FROM tarefas WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
    return task_from_row(row)


@app.get(
    "/tarefas",
    response_model=list[Task],
    dependencies=[Depends(require_api_key)],
    tags=["Tarefas"],
)
def list_tasks() -> list[Task]:
    with database() as connection:
        rows = connection.execute(
            "SELECT * FROM tarefas ORDER BY id DESC"
        ).fetchall()
    return [task_from_row(row) for row in rows]


@app.get(
    "/tarefas/{task_id}",
    response_model=Task,
    dependencies=[Depends(require_api_key)],
    tags=["Tarefas"],
)
def get_task(task_id: int) -> Task:
    with database() as connection:
        row = connection.execute(
            "SELECT * FROM tarefas WHERE id = ?", (task_id,)
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada.")
    return task_from_row(row)


@app.patch(
    "/tarefas/{task_id}",
    response_model=Task,
    dependencies=[Depends(require_api_key)],
    tags=["Tarefas"],
)
def update_task(task_id: int, payload: TaskUpdate) -> Task:
    changes = payload.model_dump(exclude_none=True)
    if not changes:
        raise HTTPException(status_code=400, detail="Nenhuma alteração informada.")

    with database() as connection:
        current = connection.execute(
            "SELECT * FROM tarefas WHERE id = ?", (task_id,)
        ).fetchone()
        if current is None:
            raise HTTPException(status_code=404, detail="Tarefa não encontrada.")

        connection.execute(
            """
            UPDATE tarefas
            SET titulo = ?, descricao = ?, prioridade = ?, concluida = ?, atualizada_em = ?
            WHERE id = ?
            """,
            (
                changes.get("titulo", current["titulo"]),
                changes.get("descricao", current["descricao"]),
                changes.get("prioridade", current["prioridade"]),
                int(changes.get("concluida", bool(current["concluida"]))),
                datetime.now(timezone.utc).isoformat(),
                task_id,
            ),
        )
        row = connection.execute(
            "SELECT * FROM tarefas WHERE id = ?", (task_id,)
        ).fetchone()
    return task_from_row(row)


@app.delete(
    "/tarefas/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_api_key)],
    tags=["Tarefas"],
)
def delete_task(task_id: int) -> Response:
    with database() as connection:
        cursor = connection.execute("DELETE FROM tarefas WHERE id = ?", (task_id,))
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
