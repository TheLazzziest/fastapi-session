import asyncio
import typing
from datetime import datetime
from functools import cached_property, lru_cache
from hashlib import sha256
from typing import Hashable

from cryptography.fernet import Fernet, InvalidToken
from fastapi import Request, Response

from .encryptors import AES_SIV_Encryptor
from .exceptions import InvalidCookieException, MissingSessionException
from .sessions import AsyncSession
from .settings import SessionSettings, get_session_settings
from .types import Connection
from .utils import create_namespace, create_backend, encrypt_session, decrypt_session


class SessionManager:
    """A manager for a session storage."""

    def __init__(
        self,
        secret: str,
        signer: typing.Type[Fernet],
        settings: typing.Type[SessionSettings],
        on_load_cookie: typing.Optional[
            typing.Callable[
                [Request, typing.Hashable],
                typing.Union[typing.Hashable, typing.Awaitable[typing.Hashable]],
            ]
        ] = None,
        backend_adapter: typing.Optional[Connection] = None,
        loop: typing.Optional[asyncio.AbstractEventLoop] = None,
    ):
        """
        :param str secret: A session secret key for encryption
        :param Fernet signer: A fernet instance for encrypting and signing session data and a cookie
        :param SessionSettingfernets settings: A session settings for the session manager
        :param Callable on_load_cookie: A callable for post processing a session cookie
        :param Connection backend_adapter: A type of backend for managing a session storage
        :param AbstractEventLoop loop: A running event loop
        """
        self._secret = secret
        self._signer = signer
        self._settings = settings
        self._backend_adapter = backend_adapter
        self._on_load_cookie = on_load_cookie
        self._loop = loop if loop is not None else asyncio.get_running_loop()

    async def __call__(self, request: Request) -> AsyncSession:
        """Try to load a user session from the incoming request."""
        if request["session"] is None:
            raise MissingSessionException(detail="A user session is missing")
        return request["session"]

    @cached_property
    def encryptor(self):
        return AES_SIV_Encryptor(
            self._secret, sha256(self._secret.encode("utf-8")).hexdigest()
        )

    async def postprocess_cookie(
        self, request: Request, cookie: typing.Hashable
    ) -> typing.Hashable:
        """Try to pass an extracted cookie to a user defined callback for postprocessing."""

        if self._on_load_cookie is None:
            return cookie

        if asyncio.iscoroutinefunction(self._on_load_cookie):
            cookie = await self._on_load_cookie(request, cookie)
        else:
            cookie = self._on_load_cookie(request, cookie)

        return cookie

    async def load_session(
        self, request: Request, session_id: Hashable
    ) -> AsyncSession:
        """Initialize a session storage for a user session."""
        return await AsyncSession.create(
            encryptor=self.encryptor,
            namespace=create_namespace(
                encryptor=self.encryptor,
                session_id=session_id,
            ),
            backend=await create_backend(
                # If this is a filesystem backend
                # then a session id will be used
                # as a source of a session file
                # @TODO: Invert resolving dependecies for a backend
                self._settings.SESSION_BACKEND,
                adapter=(
                    self._backend_adapter
                    if self._backend_adapter is not None
                    else session_id
                ),
                loop=self._loop,
            ),
            loop=self._loop,
        )

    def has_cookie(self, request: Request) -> bool:
        """Check whether a session cookie exist in the request."""
        return self._settings.SESSION_COOKIE_NAME in request.cookies

    def get_cookie(
        self, request: Request, **options: typing.Mapping[str, typing.Any]
    ) -> str:
        """Get a session cookie from the request.

        :param request: a user HTTP request
        :param timestamp: a cookie signature timestamp
        :param max_age: a cookie max age param
        """
        try:
            return decrypt_session(
                self._signer,
                request.cookies[self._settings.SESSION_COOKIE_NAME],
                (
                    options.get("max_age", self._settings.SESSION_COOKIE_MAX_AGE)
                    or options.get("expires", self._settings.SESSION_COOKIE_EXPIRES)
                ),
            )
        except InvalidToken as exc:
            raise InvalidCookieException(
                detail="Session token is outdated or malformed"
            ) from exc

    def set_cookie(
        self,
        response: Response,
        session_id: typing.Hashable,
        timestamp: typing.Optional[typing.Union[int, datetime]] = None,
        **options: typing.Mapping[str, typing.Any],
    ) -> Response:
        """Set a session cookie to the response.

        :param Response response: A fastapi response instance
        :param Hashable session_id: A generated user session id
        :param timestamp int|datetime: A cookie generation timestamp (in UTC)
        :param dict options: A set of options to override default settings
        :return Response: A modified with a set session cookie
        """

        response.set_cookie(
            self._settings.SESSION_COOKIE_NAME,
            encrypt_session(self._signer, session_id, timestamp),
            max_age=options.get("max_age", self._settings.SESSION_COOKIE_MAX_AGE),
            expires=options.get("expires", self._settings.SESSION_COOKIE_EXPIRES),
            path=options.get("path", self._settings.SESSION_COOKIE_PATH),
            domain=options.get("domain", self._settings.SESSION_COOKIE_DOMAIN),
            secure=options.get("secure", self._settings.SESSION_COOKIE_SECURE),
            httponly=options.get("httponly", self._settings.SESSION_COOKIE_HTTPONLY),
            samesite=options.get(
                "samesite", self._settings.SESSION_COOKIE_SAMESITE.value
            ),
        )
        return response

    def unset_cookie(
        self,
        response: Response,
        path: typing.Optional[str] = None,
        domain: typing.Optional[str] = None,
    ) -> Response:
        """Remove a session cookie from the response.

        :param Response response: A fastapi response instance
        :param dict options: A set of options to override default settings
        :return Response: A response with a removed session cookie
        """
        response.delete_cookie(
            self._settings.SESSION_COOKIE_NAME,
            path=path or self._settings.SESSION_COOKIE_PATH,
            domain=domain or self._settings.SESSION_COOKIE_DOMAIN,
        )
        return response


def create_session_manager(
    secret: str,
    signer: typing.Type[Fernet],
    settings: typing.Optional[typing.Type[SessionSettings]] = None,
    on_load_cookie: typing.Callable[[Request, str], typing.Awaitable[str]] = None,
    backend_adapter: typing.Optional[Connection] = None,
    loop: typing.Optional[asyncio.AbstractEventLoop] = None,
) -> SessionManager:
    """A factory method for making a session manager."""
    return SessionManager(
        secret=secret,
        signer=signer,
        settings=settings or get_session_settings(),
        on_load_cookie=on_load_cookie,
        backend_adapter=backend_adapter,
        loop=loop,
    )
