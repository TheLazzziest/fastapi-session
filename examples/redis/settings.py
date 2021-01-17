import secrets
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Dict, List, Optional

from fastapi.security import HTTPBasicCredentials
from pydantic import BaseSettings, RedisDsn

__all__ = ("Settings",)


class Settings(BaseSettings):

    # Cookie settings
    SESSION_COOKIE: str = "FAPISESSID"
    COOKIE_MAX_AGE: Optional[int] = 14 * 24 * 60 * 60
    COOKIE_EXPIRES: Optional[datetime] = datetime.now() + timedelta(days=1)  # A day
    COOKIE_DOMAIN: Optional[str] = None
    COOKIE_PATH: Optional[str] = "/"
    COOKIE_SECURE: Optional[bool] = False
    COOKIE_HTTP_ONLY: Optional[bool] = True
    COOKIE_SAME_SITE: Optional[str] = "lax"  # A

    # Session backend settings
    SECRET_KEY: str = secrets.token_urlsafe(32)
    REDIS_DSN: RedisDsn = "redis://localhost:6379/1"
