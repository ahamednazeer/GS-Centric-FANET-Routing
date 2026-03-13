from __future__ import annotations

from pathlib import Path
from sqlmodel import SQLModel, Session, create_engine

DB_PATH = Path(__file__).resolve().parent.parent / "fanet.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, echo=False)


def init_db() -> None:
    from app import models  # noqa: F401
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    return Session(engine)

