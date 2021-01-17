import asyncio
import random
import string
from base64 import b64decode, b64encode
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Awaitable, Callable, Union, Any, Optional

from itsdangerous import TimestampSigner
from itsdangerous.exc import BadTimeSignature, SignatureExpired
from fastapi import FastAPI, Cookie, Request, Response


__all__ = ("CookieSecuredMixin",)


class CookieSecuredMixin:
    """A mixin for managing security capabilities of a cookie."""

    _expires: Optional[int] = None
    _max_age: Optional[int] = None
    _domain: Optional[str] = None
    _path: Optional[str] = "/"
    _secure: Optional[bool] = False
    _http_only: Optional[bool] = False
    _same_site: Optional[str] = "lax"  # Only for a first-party

    @property
    def expires(self) -> datetime:
        return self._expires

    @expires.setter
    def set_expires(self, value: datetime) -> None:
        self._expires = value

    @property
    def max_age(self) -> None:
        return self._max_age

    @max_age.setter
    def set_max_age(self, value: int) -> None:
        self._same_site = value

    @property
    def domain(self) -> str:
        return self._domain

    @domain.setter
    def set_domain(self, value: str) -> None:
        self._domain = value

    @property
    def path(self) -> str:
        return self._path

    @path.setter
    def set_path(self, value: str) -> None:
        self._path = value

    @property
    def secure(self) -> str:
        return self._secure

    @secure.setter
    def set_secure(self, value: bool) -> None:
        self._secure = value

    @property
    def http_only(self) -> bool:
        return self._http_only

    @http_only.setter
    def set_http_only(self, value: bool) -> None:
        self._http_only = value

    @property
    def same_site(self) -> str:
        return self._same_site

    @same_site.setter
    def same_site(self, value: str) -> None:
        # Values: Strict, Lax, None
        self._same_site = value

    def __str__(self):
        # @TODO: Implement it!!!
        return f"Expires={self.expires};Max-Age={self.max_age};Domain={self.domain};"
