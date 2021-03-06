import typing
import secrets
from base64 import b64encode
from datetime import datetime
from hashlib import sha256
from unittest.mock import AsyncMock

import pytest
from cryptography.fernet import Fernet
from fastapi import FastAPI, Request, Response, HTTPException, status
from fastapi_session import (
    decrypt_session,
    encrypt_session,
    SessionManager,
    SessionSettings,
    SessionMiddleware,
)
from pytest_mock import MockerFixture
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_handling_valid_cookie(
    signer: typing.Type[Fernet],
    secret: str,
    session_id: str,
    app: FastAPI,
    settings: SessionSettings,
    mocker: MockerFixture,
):
    """
    Check that a session middleware handles a request with a valid cookie
    """

    on_load_cookie_mock = AsyncMock(return_value=session_id)
    manager = SessionManager(
        secret=secret,
        signer=signer,
        settings=settings,
        on_missing_session=AsyncMock(
            side_effect=HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        ),
    )
    app.add_middleware(
        SessionMiddleware,
        manager=manager,
        on_load_cookie=on_load_cookie_mock,
        on_invalid_cookie=AsyncMock(
            return_value=Response(status_code=status.HTTP_400_BAD_REQUEST)
        ),
    )
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        response = await client.get(
            "/",
            cookies={settings.COOKIE_NAME: encrypt_session(signer, session_id)},
        )
        assert on_load_cookie_mock.called is True


@pytest.mark.asyncio
async def test_handling_invalid_cookie(
    signer: typing.Type[Fernet],
    secret: str,
    session_id: str,
    app: FastAPI,
    settings: SessionSettings,
):
    """
    Check that a session middleware handles a request with an invalid cookie
    """

    on_invalid_cookie_mock = AsyncMock(
        return_value=Response(status_code=status.HTTP_400_BAD_REQUEST)
    )
    manager = SessionManager(
        secret=secret,
        signer=signer,
        settings=settings,
        on_missing_session=AsyncMock(
            side_effect=HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        ),
    )
    app.add_middleware(
        SessionMiddleware,
        manager=manager,
        on_load_cookie=AsyncMock(return_value=secrets.token_urlsafe(8)),
        on_invalid_cookie=on_invalid_cookie_mock,
    )
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        response = await client.get(
            "/",
            cookies={
                # Try to temper a user session id
                settings.COOKIE_NAME: sha256(session_id.encode("utf-8")).hexdigest()
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert on_invalid_cookie_mock.called is True


@pytest.mark.asyncio
async def test_ignoring_invalid_cookie(
    signer: typing.Type[Fernet],
    secret: str,
    session_id: str,
    app: FastAPI,
    settings: SessionSettings,
):
    """
    Check that a session middleware ignores a request with an invalid cookie
    """

    async def index(response: Response) -> Response:
        response.status_code = status.HTTP_200_OK
        return response

    session = SessionManager(
        secret=secret,
        signer=signer,
        settings=settings,
        on_missing_session=AsyncMock(
            side_effect=HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        ),
    )
    app.add_middleware(
        SessionMiddleware,
        manager=session,
        on_load_cookie=AsyncMock(return_value=session_id),
    )

    app.add_api_route("/", index)

    async with AsyncClient(app=app, base_url="http://testserver") as client:
        response = await client.get(
            "/",
            cookies={
                # Try to temper a user session id
                settings.COOKIE_NAME: sha256(session_id.encode("utf-8")).hexdigest(),
            },
        )
        assert response.status_code == status.HTTP_200_OK
