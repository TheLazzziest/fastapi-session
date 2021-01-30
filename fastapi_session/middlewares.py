import json
import typing

from fastapi import FastAPI, Request, Response, HTTPException, status
from itsdangerous.exc import BadTimeSignature, SignatureExpired, BadSignature

from starlette.types import Receive, Scope, Send

from .managers import SessionManager

__all__ = ("SessionMiddleware",)


class SessionMiddleware:
    """A middleware for initializing and managing a user session."""

    def __init__(
        self,
        app: FastAPI,
        manager: SessionManager,
        on_load_cookie: typing.Callable[[Request, str], typing.Awaitable[str]],
        on_invalid_cookie: typing.Optional[
            typing.Callable[
                [Request, typing.Type[Exception]], typing.Awaitable[Response]
            ]
        ] = None,
        on_undefined_error: typing.Optional[
            typing.Callable[[Request], typing.Awaitable]
        ] = None,
    ) -> "SessionMiddleware":
        """
        :param app: A fastapi app instance
        :param manager: An instance of SessionManager
        :param on_load_cookie: A callback for doing some user defined preprocessing of a session cookie
        :param on_invalid_cookie: A callback for handling a case of passing an invalid cookie
        :param on_undefined_error: A callback for handling some errors occured during request processing
        """
        self.app = app
        self.manager = manager
        # A set of user callbacks for
        self.on_load_cookie = on_load_cookie
        self.on_invalid_cookie = on_invalid_cookie
        self.on_undefined_error = on_undefined_error

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):  # pragma: no cover
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive, send)
        if not self.manager.has_session_cookie(request):
            await self.app(scope, receive, send)
            return

        try:
            scope["session"] = await self.manager.load_session(
                await self.on_load_cookie(
                    request, self.manager.get_session_cookie(request)
                )
            )
        except (BadSignature, BadTimeSignature, SignatureExpired) as exc:
            if not self.on_invalid_cookie:
                return await self.app(scope, receive, send)
            response: Response = await self.on_invalid_cookie(request, exc)
            if response is not None:
                if scope["type"] == "websocket":
                    await send({"type": "websocket.close", "code": 1000})
                else:
                    await response(scope, receive, send)
                return
        except Exception as exc:
            if self.on_undefined_error:
                await self.on_undefined_error(request, exc)

        await self.app(scope, receive, send)
