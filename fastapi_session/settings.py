"""A module which contains settings for managing different parts of session storage."""
import typing
from functools import lru_cache

from pydantic import BaseSettings, validator

from .enums import SameSiteEnum
from .constants import FS_BACKEND_TYPE

__all__ = ("SessionSettings", "get_session_settings")


class SessionSettings(BaseSettings):
    # Session settings
    SESSION_BACKEND: typing.Optional[str] = FS_BACKEND_TYPE
    # Cookie settings
    SESSION_COOKIE_NAME: typing.Optional[str] = "FAPISESSID"
    SESSION_COOKIE_EXPIRES: typing.Optional[int] = None
    SESSION_COOKIE_DOMAIN: typing.Optional[str] = None
    SESSION_COOKIE_HTTPONLY: typing.Optional[bool] = False
    #  If both EXPIRES and MAX_AGE are set, MAX_AGE has precedence.
    SESSION_COOKIE_MAX_AGE: typing.Optional[int] = None
    SESSION_COOKIE_PATH: typing.Optional[str] = "/"
    SESSION_COOKIE_SAMESITE: typing.Optional[
        SameSiteEnum
    ] = SameSiteEnum.lax.value  # Only for a first-party
    SESSION_COOKIE_SECURE: typing.Optional[bool] = False

    @validator("SESSION_COOKIE_SAMESITE", pre=True, allow_reuse=True)
    def validate_cookie_samesite(cls, v: typing.Optional[str]) -> SameSiteEnum:
        if v not in {"strict", "lax", "none"}:
            raise ValueError(
                f"Value {v} for SAMESITE must be one of the following: 'strict', 'lax', 'none'"
            )
        return SameSiteEnum(v)


@lru_cache
def get_session_settings():
    return SessionSettings()