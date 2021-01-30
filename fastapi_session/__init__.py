import asyncio
import typing

from fastapi import FastAPI, Request, Response

from .backends import (
    BackendInterface,
    DBBackend,
    FSBackend,
    RedisBackend,
)
from .constants import FS_BACKEND_TYPE, DATABASE_BACKEND_TYPE, REDIS_BACKEND_TYPE
from .dependencies import get_session_manager, get_user_session
from .managers import SessionManager, create_session_manager
from .middlewares import SessionMiddleware
from .session import AsyncSession
from .settings import get_session_settings, SessionSettings
from .types import Connection

__all__ = (
    BackendInterface,
    "connect",
    Connection,
    create_session_manager,
    DBBackend,
    DATABASE_BACKEND_TYPE,
    FSBackend,
    FS_BACKEND_TYPE,
    get_session_manager,
    get_session_settings,
    get_user_session,
    RedisBackend,
    REDIS_BACKEND_TYPE,
    SessionManager,
    SessionManager,
    SessionMiddleware,
)


def connect(
    app: FastAPI,
    secret_key: typing.Hashable,
    on_load_cookie: typing.Callable[[Request, str], typing.Awaitable[str]],
    on_missing_session: typing.Callable[[Request], typing.Awaitable],
    settings: typing.Optional[typing.Type[SessionSettings]] = None,
    backend_adapter_loader: typing.Optional[
        typing.Callable[[FastAPI], Connection]
    ] = None,
    on_invalid_cookie: typing.Optional[
        typing.Callable[[Request, typing.Type[Exception]], typing.Awaitable[Response]]
    ] = None,
    on_undefined_error: typing.Optional[
        typing.Callable[[Request], typing.Awaitable[None]]
    ] = None,
    loop: typing.Optional[asyncio.AbstractEventLoop] = None,
) -> None:
    """An adapter to connect session components to a FastAPI instance.

    :param FastAPI app:
    :param Hashable secret_key:
    :param Callable on_load_cookie:
    :param SessionSettings settings:
    :param Connection backend_adapter:
    :param Callable leon_invalid_cookie:
    :param Callable on_undefined_error:
    :param AbstractEventLoop loop:
    """

    @app.on_event("startup")
    async def on_startup():
        app.state.session = SessionManager(
            secret_key,
            settings=settings or get_session_settings(),
            backend_adapter=(
                backend_adapter_loader(app) if backend_adapter_loader else None
            ),
            on_missing_session=on_missing_session,
            loop=loop,
        )

        app.add_middleware(
            SessionMiddleware,
            manager=app.state.session,
            on_load_cookie=on_load_cookie,
            on_invalid_cookie=on_invalid_cookie,
            on_undefined_error=on_undefined_error,
        )
