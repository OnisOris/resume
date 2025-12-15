from __future__ import annotations

from fastapi import Depends, Header, HTTPException, status
from sqlmodel import Session

from .config import Settings, get_settings
from .database import get_session


def get_db_session() -> Session:
    yield from get_session()


def require_admin(
    admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
    settings: Settings = Depends(get_settings),
) -> None:
    if settings.admin_token == "change-me":
        raise HTTPException(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            detail="Установите APP_ADMIN_TOKEN в .env перед использованием админки.",
        )
    if not admin_token or admin_token != settings.admin_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный admin token")
