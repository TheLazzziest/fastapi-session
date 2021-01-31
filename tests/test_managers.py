import pytest
import secrets
import typing
from base64 import b64encode
from unittest.mock import AsyncMock

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.testclient import TestClient
from fastapi_session import (
    AsyncSession,
    connect,
    create_session_manager,
    FSBackend,
    get_session_manager,
    SessionManager,
    SessionSettings,
)


@pytest.mark.asyncio
async def test_session_backend(
    settings: SessionSettings,
):

    manager = SessionManager(
        secret_key=secrets.token_urlsafe(32),
        settings=settings,
        on_missing_session=AsyncMock(
            side_effect=HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        ),
    )

    session = await manager.load_session(secrets.token_urlsafe(8))

    assert isinstance(session, AsyncSession)
    assert isinstance(session.backend, FSBackend)


@pytest.mark.asyncio
async def test_session_manager_factory():

    manager = create_session_manager(
        secret_key=secrets.token_urlsafe(32),
        on_missing_session=AsyncMock(
            return_value=Response(status_code=status.HTTP_401_UNAUTHORIZED)
        ),
    )

    session = await manager.load_session(secrets.token_urlsafe(8))

    assert isinstance(session, AsyncSession)
    assert isinstance(session.backend, FSBackend)


def test_open_session(session_id: str, app: FastAPI, settings: SessionSettings):
    async def index(
        response: Response, manager: SessionManager = Depends(get_session_manager)
    ) -> Response:
        response.status_code = status.HTTP_200_OK
        return manager.open_session(response, session_id)

    connect(
        app=app,
        secret_key=secrets.token_urlsafe(32),
        on_load_cookie=AsyncMock(return_value=session_id),
        on_missing_session=AsyncMock(
            side_effect=HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        ),
    )
    app.add_api_route("/", index)
    with TestClient(app=app) as client:
        response = client.get("/")
        assert response.status_code == status.HTTP_200_OK
        assert settings.SESSION_COOKIE in response.cookies


def test_close_session(session_id: str, app: FastAPI, settings: SessionSettings):
    async def index(
        response: Response, manager: SessionManager = Depends(get_session_manager)
    ) -> Response:
        response.status_code = status.HTTP_200_OK
        return manager.close_session(response)

    connect(
        app=app,
        secret_key=secrets.token_urlsafe(32),
        on_load_cookie=AsyncMock(return_value=session_id),
        on_missing_session=AsyncMock(
            side_effect=HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        ),
    )
    app.add_api_route("/", index)
    with TestClient(app=app) as client:
        response = client.get(
            "/",
            cookies={
                settings.SESSION_COOKIE: b64encode(
                    app.state.session.signer.sign(session_id)
                ).decode("utf-8")
            },
        )
        assert response.status_code == status.HTTP_200_OK
        assert settings.SESSION_COOKIE not in response.cookies
