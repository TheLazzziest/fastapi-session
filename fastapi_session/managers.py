import asyncio
import typing
from base64 import b64decode, b64encode
from dataclasses import dataclass, field
from functools import cached_property, lru_cache
from typing import Hashable

from fastapi import Request, Response
from itsdangerous import TimestampSigner

from .session import AsyncSession
from .settings import SessionSettings, get_session_settings
from .types import Connection


class SessionManager:
    """A manager for a session storage."""

    def __init__(
        self,
        secret_key: typing.Hashable,
        settings: typing.Type[SessionSettings],
        on_missing_session: typing.Callable[[Request], typing.Awaitable],
        backend_adapter: typing.Optional[Connection] = None,
        loop: typing.Optional[asyncio.AbstractEventLoop] = None,
    ):
        """
        :param Hashable secret_key: A session secret key for signing a session cookie
        :param SessionSettings settings: A session settings for the session manager
        :param Callable on_missing_session: A callable for runnning a user defined behaviour in case of missing a session in the incomming request
        :param Connection backend_adapter: A type of backend for managing a session storage
        :param AbstractEventLoop loop: A running event loop
        """
        self._secret_key = secret_key
        self._settings = settings
        self._backend_adapter = backend_adapter
        self._on_missing_session = on_missing_session
        self._loop = loop

    async def __call__(self, request: Request) -> AsyncSession:
        """Try to load a user session from the incoming request."""
        if "session" not in request:
            await self._on_missing_session(request)
        return request.session

    async def load_session(self, session_id: Hashable) -> AsyncSession:
        """Initialize a session storage for a user session."""
        return await AsyncSession.create(
            secret_key=self._secret_key,
            session_id=session_id,
            backend=self._settings.SESSION_BACKEND,
            backend_kwargs={
                # If this is a filesystem backend
                # then a session id will be used
                # as a source of a session file
                "adapter": (
                    self._backend_adapter if self._backend_adapter else session_id
                ),
            },
            loop=self._loop,
        )

    @cached_property
    def signer(self) -> TimestampSigner:
        """Cookie security signer."""
        return TimestampSigner(str(self._secret_key))

    def has_session_cookie(self, request: Request) -> bool:
        """Check whether a session cookie exist in the request."""
        return self._settings.SESSION_COOKIE in request.cookies

    def get_session_cookie(
        self, request: Request, **options: typing.Mapping[str, typing.Any]
    ) -> str:
        """Get a session cookie from the request."""
        signed_id = b64decode(
            request.cookies[self._settings.SESSION_COOKIE].encode("utf-8")
        )
        return self.signer.unsign(
            signed_id, max_age=options.get("max_age", self._settings.MAX_AGE)
        ).decode("utf-8")

    def open_session(
        self,
        response: Response,
        session_id: typing.Hashable,
        **options: typing.Mapping[str, typing.Any]
    ) -> Response:
        """Set a session cookie to the response.

        :param Response response: A fastapi response instance
        :param Hashable session_id: A generated user session id
        :param dict options: A set of options to override default settings
        :return Response: A modified with a set session cookie
        """
        signed_id = self.signer.sign(session_id)
        response.set_cookie(
            self._settings.SESSION_COOKIE,
            b64encode(signed_id).decode("utf-8"),
            max_age=options.get("max_age", self._settings.MAX_AGE),
            expires=options.get("expires", self._settings.EXPIRES),
            path=options.get("path", self._settings.PATH),
            domain=options.get("domain", self._settings.DOMAIN),
            secure=options.get("secure", self._settings.SECURE),
            httponly=options.get("httponly", self._settings.HTTP_ONLY),
            samesite=options.get("samesite", self._settings.SAME_SITE),
        )
        return response

    def close_session(
        self, response: Response, **options: typing.Mapping[str, typing.Any]
    ) -> Response:
        """Remove a session cookie from the response.

        :param Response response: A fastapi response instance
        :param dict options: A set of options to override default settings
        :return Response: A response with a removed session cookie
        """
        response.delete_cookie(
            self._settings.SESSION_COOKIE,
            path=options.get("path", self._settings.PATH),
            domain=options.get("domain", self._settings.DOMAIN),
        )
        return response


@lru_cache
def create_session_manager(
    secret_key: typing.Hashable,
    on_missing_session: typing.Callable[[Request], typing.Awaitable],
    settings: typing.Optional[typing.Type[SessionSettings]] = None,
    backend_adapter: typing.Optional[Connection] = None,
    loop: typing.Optional[asyncio.AbstractEventLoop] = None,
) -> SessionManager:
    """A factory method for making a session manager."""
    return SessionManager(
        secret_key=secret_key,
        settings=settings or get_session_settings(),
        backend_adapter=backend_adapter,
        on_missing_session=on_missing_session,
        loop=loop,
    )
