from __future__ import annotations

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db_session


def get_settings_dep() -> Settings:
    return get_settings()


def get_db(session: Session = Depends(get_db_session)) -> Session:
    return session


def require_admin(x_admin_token: str | None = Header(default=None), settings: Settings = Depends(get_settings_dep)) -> None:
    if x_admin_token != settings.admin_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin token")
