import pytest
import secrets
import typing
from base64 import b64encode
from unittest.mock import AsyncMock, Mock

from cryptography.fernet import Fernet
from fastapi import FastAPI, Depends, HTTPException, Request, Response, status
from fastapi.testclient import TestClient
from fastapi_session import (
    AsyncSession,
    create_session_manager,
    encrypt_session,
    FSBackend,
    get_session_manager,
    SessionManager,
    SessionSettings,
)
from fastapi_session.adapters.fastapi import connect


@pytest.mark.asyncio
async def test_session_backend(
    secret: str,
    signer: typing.Type[Fernet],
    settings: SessionSettings,
):

    manager = SessionManager(secret=secret, signer=signer, settings=settings)

    session = await manager.load_session(
        request=Mock(), session_id=secrets.token_urlsafe(8)
    )

    assert isinstance(session, AsyncSession) is True
    assert isinstance(session._backend, FSBackend) is True


@pytest.mark.asyncio
async def test_session_manager_factory(secret: str, signer: typing.Type[Fernet]):

    manager = create_session_manager(secret=secret, signer=signer)

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
        return manager.set_cookie(response, session_id)

    connect(
        secret=secret,
        app=app,
        signer=signer,
        on_load_cookie=AsyncMock(return_value=session_id),
    )
    app.add_api_route("/", index)
    with TestClient(app=app) as client:
        response = client.get("/")
        assert response.status_code == status.HTTP_200_OK
        assert settings.SESSION_COOKIE_NAME in response.cookies


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
        return manager.unset_cookie(response)

    connect(
        app=app,
        secret=secret,
        signer=signer,
        on_load_cookie=AsyncMock(return_value=session_id),
    )
    app.add_api_route("/", index)
    with TestClient(app=app) as client:
        response = client.get(
            "/",
            cookies={settings.SESSION_COOKIE_NAME: encrypt_session(signer, session_id)},
        )
        assert response.status_code == status.HTTP_200_OK
        assert settings.SESSION_COOKIE_NAME not in response.cookies
