import typing
import secrets
from base64 import b64encode
from datetime import datetime
from hashlib import sha256
from unittest.mock import AsyncMock

import pytest
from cryptography.fernet import Fernet
from fastapi import FastAPI, Request, Depends, Response, HTTPException, status
from fastapi_session import (
    decrypt_session,
    encrypt_session,
    get_session_manager,
    InvalidCookieException,
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
        on_load_cookie=on_load_cookie_mock,
    )
    app.add_middleware(
        SessionMiddleware,
        manager=manager,
    )
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        response = await client.get(
            "/",
            cookies={settings.SESSION_COOKIE_NAME: encrypt_session(signer, session_id)},
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
    manager = SessionManager(
        secret=secret,
        signer=signer,
        settings=settings,
        on_load_cookie=AsyncMock(return_value=secrets.token_urlsafe(8)),
    )
    app.add_middleware(SessionMiddleware, manager=manager, strict=True)
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        with pytest.raises(InvalidCookieException):
            response = await client.get(
                "/",
                cookies={
                    # Try to temper a user session id
                    settings.SESSION_COOKIE_NAME: sha256(
                        session_id.encode("utf-8")
                    ).hexdigest()
                },
            )
            assert response.status_code == status.HTTP_400_BAD_REQUEST


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
        on_load_cookie=AsyncMock(return_value=session_id),
    )
    app.add_middleware(
        SessionMiddleware,
        manager=session,
    )

    app.add_api_route("/", index)

    async with AsyncClient(app=app, base_url="http://testserver") as client:
        response = await client.get(
            "/",
            cookies={
                # Try to temper a user session id
                settings.SESSION_COOKIE_NAME: sha256(
                    session_id.encode("utf-8")
                ).hexdigest(),
            },
        )
        assert response.status_code == status.HTTP_200_OK
