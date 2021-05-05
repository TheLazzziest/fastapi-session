import asyncio
import typing

from fastapi import FastAPI, Request, Response
from cryptography.fernet import Fernet

from ..managers import create_session_manager
from ..middlewares import SessionMiddleware
from ..settings import SessionSettings
from ..types import Connection


def connect(
    app: FastAPI,
    secret: str,
    signer: typing.Type[Fernet],
    on_load_cookie: typing.Callable[[Request, str], typing.Awaitable[str]],
    settings: typing.Optional[typing.Type[SessionSettings]] = None,
    backend_adapter_loader: typing.Optional[
        typing.Callable[[FastAPI], Connection]
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
        app.session = create_session_manager(
            secret=secret,
            signer=signer,
            settings=settings,
            backend_adapter=(
                backend_adapter_loader(app) if backend_adapter_loader else None
            ),
            on_load_cookie=on_load_cookie,
            loop=loop,
        )

        app.add_middleware(
            SessionMiddleware,
            manager=app.session,
        )
