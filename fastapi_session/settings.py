"""A module which contains settings for managing different parts of session storage."""
import typing
from functools import lru_cache

from pydantic import BaseSettings, validator

from .constants import FS_BACKEND_TYPE

__all__ = ("SessionSettings", "get_session_settings")


class SessionSettings(BaseSettings):
    # Session settings
    SESSION_BACKEND: typing.Optional[str] = FS_BACKEND_TYPE
    # Cookie settings
    COOKIE_NAME: typing.Optional[str] = "FAPISESSID"
    EXPIRES: typing.Optional[int] = None
    DOMAIN: typing.Optional[str] = None
    HTTP_ONLY: typing.Optional[bool] = False
    #  If both EXPIRES and MAX_AGE are set, MAX_AGE has precedence.
    MAX_AGE: typing.Optional[int] = None
    COOKIE_PATH: typing.Optional[str] = "/"
    SAME_SITE: typing.Optional[str] = "lax"  # Only for a first-party
    SECURE: typing.Optional[bool] = False


@lru_cache
def get_session_settings():
    return SessionSettings()