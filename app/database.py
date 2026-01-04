import os
from typing import Iterator

from sqlmodel import Session, SQLModel, create_engine

from app.config import BASE_DIR


def _build_engine():
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        return create_engine(db_url, echo=False)

    sqlite_file = BASE_DIR / "data.db"
    sqlite_file.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(
        f"sqlite:///{sqlite_file}", echo=False, connect_args={"check_same_thread": False}
    )


engine = _build_engine()


def init_db() -> None:
    """Cria as tabelas caso ainda não existam."""
    from app import models  # noqa: F401

    SQLModel.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    """Dependency do FastAPI para fornecer sessão do banco."""
    with Session(engine) as session:
        yield session

