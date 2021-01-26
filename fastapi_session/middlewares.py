import json
import typing

from fastapi import FastAPI, Request, Response
from itsdangerous.exc import BadTimeSignature, SignatureExpired, BadSignature

from starlette.types import Receive, Scope, Send

from .managers import SessionManager

__all__ = ("SessionMiddleware",)


class SessionMiddleware:
    """A middleware for configuring and managing a session storage."""

    def __init__(
        self,
        app: FastAPI,
        manager: SessionManager,
        on_invalid_cookie: typing.Optional[
            typing.Callable[
                [Request, typing.Union[BadTimeSignature, SignatureExpired]], Response
            ]
        ] = None,
    ) -> "SessionMiddleware":
        """
        :param app: A fastapi app instance
        :param manager: An instance of SessionManager
        :param on_invalid_cookie: A callback for handling a case of passing an invalid cookie
        """
        self.app = app
        self.manager = manager
        self.on_invalid_cookie = on_invalid_cookie

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):  # pragma: no cover
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive, send)
        if not self.manager.has_session(request):
            await self.app(scope, receive, send)
            return

        try:
            scope["session"] = await self.manager.load_session(
                self.manager.get_session(request)
            )
        except (BadSignature, BadTimeSignature, SignatureExpired) as exc:
            if not self.on_invalid_cookie:
                return await self.app(scope, receive, send)
            response = self.on_invalid_cookie(request, exc)
            if scope["type"] == "websocket":
                await send({"type": "websocket.close", "code": 1000})
            else:
                await response(scope, receive, send)
            return
        except Exception as exc:
            raise RuntimeError("Internal server error occured") from exc

        await self.app(scope, receive, send)
