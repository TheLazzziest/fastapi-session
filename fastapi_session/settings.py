"""A module which contains settings for managing different parts of session storage."""
import typing
from functools import lru_cache

from pydantic import BaseSettings

from .constants import FS_BACKEND_TYPE

__all__ = ("SessionSettings", "get_session_settings")


class SessionSettings(BaseSettings):
    # Session settings
    SESSION_BACKEND: typing.Optional[str] = FS_BACKEND_TYPE
    # Cookie settings
    SESSION_COOKIE: typing.Optional[str] = "FAPISESSID"
    MAX_AGE: typing.Optional[int] = None
    EXPIRES: typing.Optional[int] = None
    DOMAIN: typing.Optional[str] = None
    PATH: typing.Optional[str] = "/"
    SECURE: typing.Optional[bool] = False
    HTTP_ONLY: typing.Optional[bool] = False
    SAME_SITE: typing.Optional[str] = "lax"  # Only for a first-party

    class Config:
        env_prefix = "fapi_"


@lru_cache
def get_session_settings():
    return SessionSettings()