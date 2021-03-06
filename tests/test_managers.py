import pytest
import secrets
import typing
from base64 import b64encode
from unittest.mock import AsyncMock

from cryptography.fernet import Fernet
from fastapi import FastAPI, Depends, HTTPException, Request, Response, status
from fastapi.testclient import TestClient
from fastapi_session import (
    AsyncSession,
    connect,
    create_session_manager,
    encrypt_session,
    FSBackend,
    get_session_manager,
    SessionManager,
    SessionSettings,
)


@pytest.mark.asyncio
async def test_session_backend(
    secret: str,
    signer: typing.Type[Fernet],
    settings: SessionSettings,
):

    manager = SessionManager(
        secret=secret,
        signer=signer,
        settings=settings,
        on_missing_session=AsyncMock(
            side_effect=HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        ),
    )

    session = await manager.load_session(secrets.token_urlsafe(8))

    assert isinstance(session, AsyncSession) is True
    assert isinstance(session._backend, FSBackend) is True


@pytest.mark.asyncio
async def test_session_manager_factory(secret: str, signer: typing.Type[Fernet]):

    manager = create_session_manager(
        secret=secret,
        signer=signer,
        on_missing_session=AsyncMock(
            return_value=Response(status_code=status.HTTP_401_UNAUTHORIZED)
        ),
    )

    assert isinstance(manager, SessionManager) is True


def test_open_session(
    signer: typing.Type[Fernet],
    secret: str,
    session_id: str,
    app: FastAPI,
    settings: SessionSettings,
):
    async def index(
        response: Response, manager: SessionManager = Depends(get_session_manager)
    ) -> Response:
        response.status_code = status.HTTP_200_OK
        return manager.open_session(response, session_id)

    connect(
        secret=secret,
        app=app,
        signer=signer,
        on_load_cookie=AsyncMock(return_value=session_id),
        on_missing_session=AsyncMock(
            side_effect=HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        ),
    )
    app.add_api_route("/", index)
    with TestClient(app=app) as client:
        response = client.get("/")
        assert response.status_code == status.HTTP_200_OK
        assert settings.COOKIE_NAME in response.cookies


def test_close_session(
    signer: typing.Type[Fernet],
    secret: str,
    session_id: str,
    app: FastAPI,
    settings: SessionSettings,
):
    async def index(
        response: Response, manager: SessionManager = Depends(get_session_manager)
    ) -> Response:
        response.status_code = status.HTTP_200_OK
        return manager.close_session(response)

    connect(
        app=app,
        secret=secret,
        signer=signer,
        on_load_cookie=AsyncMock(return_value=session_id),
        on_missing_session=AsyncMock(
            side_effect=HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        ),
    )
    app.add_api_route("/", index)
    with TestClient(app=app) as client:
        response = client.get(
            "/",
            cookies={settings.COOKIE_NAME: encrypt_session(signer, session_id)},
        )
        assert response.status_code == status.HTTP_200_OK
        assert settings.COOKIE_NAME not in response.cookies
