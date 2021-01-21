import json
import typing

from fastapi import FastAPI, Request, Response
from itsdangerous.exc import BadTimeSignature, SignatureExpired, BadSignature

from starlette.types import Message, Receive, Scope, Send

from .managers import SessionManager, CookieManager

__all__ = ("SessionMiddleware",)


class CookieSessionMiddleware:
    """A middleware for configuring and managing session storage."""

    def __init__(
        self,
        app: FastAPI,
        cookie_manager: CookieManager,
        session_manager: SessionManager,
        on_invalid_cookie: typing.Optional[
            typing.Callable[
                [Request, typing.Union[BadTimeSignature, SignatureExpired]], Response
            ]
        ] = None,
    ) -> None:
        """
        :param app: A fastapi app instance
        :param cookie_manager: An instance of a cookie manager
        :param session_manager: An instance of a session_manager
        :param on_invalid_cookie: A callback for handling a case of passing an invalid cookie
        """
        self.app = app
        self.cookie_manager = cookie_manager
        self.session_manager = session_manager
        self.on_invalid_cookie = on_invalid_cookie

    def get_request(self, scope: Scope, receive: Receive, send: Send) -> Request:
        return Request(scope, receive, send)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):  # pragma: no cover
            await self.app(scope, receive, send)
            return

        request = self.get_request(scope, receive, send)
        if not self.cookie_manager.has_cookie(request):
            await self.app(scope, receive, send)
            return

        try:
            cookie = self.cookie_manager.get_cookie(request)
            scope["session"] = await self.session_manager.load_session(
                scope["app"],
                cookie,
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
