from __future__ import annotations

from typing import Iterator

from sqlalchemy import inspect, text

from sqlmodel import Session, SQLModel, create_engine

from .config import Settings, get_settings

engine = None


def init_engine(url: str | None = None, settings: Settings | None = None):
    global engine
    if engine is None:
        settings = settings or get_settings()
        database_url = url or settings.resolved_database_url
        connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
        engine = create_engine(database_url, connect_args=connect_args)
    return engine


def get_session() -> Iterator[Session]:
    if engine is None:
        raise RuntimeError("База данных не инициализирована")
    with Session(engine) as session:
        yield session


def create_db_and_tables() -> None:
    if engine is None:
        raise RuntimeError("База данных не инициализирована")
    SQLModel.metadata.create_all(engine)


def ensure_wishlist_columns() -> None:
    """Простая миграция: добавляем колонку image_path при необходимости."""
    if engine is None:
        raise RuntimeError("База данных не инициализирована")
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    if "wishitem" not in tables:
        return
    columns = {col["name"] for col in inspector.get_columns("wishitem")}
    if "image_path" not in columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE wishitem ADD COLUMN image_path VARCHAR"))


def get_engine():
    if engine is None:
        raise RuntimeError("База данных не инициализирована")
    return engine
