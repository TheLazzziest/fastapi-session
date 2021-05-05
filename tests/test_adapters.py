import pytest
import secrets
import typing
from unittest.mock import AsyncMock, patch

from cryptography.fernet import Fernet
from fastapi import FastAPI, HTTPException, Response, status
from fastapi.testclient import TestClient
from fastapi_session import SessionManager, SessionMiddleware, SessionSettings
from fastapi_session.adapters.fastapi import connect
from starlette.types import Receive, Scope, Send


def test_fastapi_adapter(
    secret: str, signer: typing.Type[Fernet], app: FastAPI, settings: SessionSettings
):
    async def index() -> Response:
        return Response(status_code=status.HTTP_400_BAD_REQUEST)

    async def middleware_callable(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        await send(
            {
                "type": "http.response.start",
                "status": status.HTTP_200_OK,
                "headers": [],
            }
        )

    connect(
        app=app,
        secret=secret,
        signer=signer,
        on_load_cookie=AsyncMock(return_value=lambda request, cookie: cookie),
    )
    app.add_api_route("/", index)

    with patch.object(SessionMiddleware, "__call__", new=middleware_callable):
        with TestClient(app) as client:
            response = client.get("/")
            assert (
                response.status_code is status.HTTP_200_OK
            )  # indicates that mock in SessionMiddleware has been worked
            assert hasattr(app, "session") is True
            assert isinstance(app.session, SessionManager) is True
