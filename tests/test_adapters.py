import pytest
import secrets
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI, HTTPException, Response, status
from fastapi.testclient import TestClient
from fastapi_session import connect, SessionManager, SessionMiddleware, SessionSettings
from starlette.types import Receive, Scope, Send


def test_fastapi_adapter(app: FastAPI, settings: SessionSettings):
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

    secret_key = secrets.token_urlsafe(32)
    connect(
        app=app,
        secret_key=secret_key,
        on_load_cookie=AsyncMock(return_value=lambda request, cookie: cookie),
        on_missing_session=AsyncMock(
            side_effect=HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        ),
    )
    app.add_api_route("/", index)

    with patch.object(SessionMiddleware, "__call__", new=middleware_callable):
        with TestClient(app) as client:
            response = client.get("/")
            assert (
                response.status_code is status.HTTP_200_OK
            )  # indicates that mock in SessionMiddleware has been worked
            assert hasattr(app.state, "session") is True
            assert isinstance(app.state.session, SessionManager)
