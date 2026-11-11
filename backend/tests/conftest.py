import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app import models  # noqa: F401  (registra las tablas en Base.metadata)
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.status import Status

STATUS_SEED = [
    (1, "created", "Creada", 1, False),
    (2, "in_review", "En revisión", 2, False),
    (3, "in_progress", "En progreso", 3, False),
    (4, "paused", "Pausada", 4, False),
    (5, "done", "Finalizada", 5, True),
]


@pytest.fixture()
def session_factory() -> sessionmaker[Session]:
    """SQLite en memoria: rápido y aislado para los tests de integración.

    En producción se usa MySQL (schema.sql); los tests de integración contra
    MySQL se documentan aparte.
    """
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    with factory() as session:
        session.add_all(
            Status(
                id=status_id,
                code=code,
                label=label,
                sort_order=sort_order,
                is_final=is_final,
            )
            for status_id, code, label, sort_order, is_final in STATUS_SEED
        )
        session.commit()

    yield factory

    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture()
def client(session_factory: sessionmaker[Session]) -> TestClient:
    def override_get_db():
        with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
