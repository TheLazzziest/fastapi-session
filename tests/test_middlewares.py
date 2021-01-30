import typing
import secrets
from base64 import b64encode
from unittest.mock import AsyncMock

import pytest

from itsdangerous import BadTimeSignature, SignatureExpired
from fastapi import FastAPI, Request, Response, HTTPException, status
from fastapi_session import (
    SessionManager,
    SessionSettings,
    SessionMiddleware,
)
from pytest_mock import MockerFixture
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_handling_valid_cookie(
    session_id: str, app: FastAPI, settings, mocker: MockerFixture
):
    """
    Check that a session middleware handles a request with a valid cookie
    """

    on_valid_cookie_mock = AsyncMock(return_value=session_id)
    secret_key = secrets.token_urlsafe(32)
    manager = SessionManager(
        secret_key=secret_key,
        settings=settings,
        on_missing_session=AsyncMock(
            side_effect=HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        ),
    )
    app.add_middleware(
        SessionMiddleware,
        manager=manager,
        on_load_cookie=on_valid_cookie_mock,
        on_invalid_cookie=AsyncMock(
            return_value=Response(status_code=status.HTTP_400_BAD_REQUEST)
        ),
    )
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        response = await client.get(
            "/",
            cookies={
                settings.SESSION_COOKIE: b64encode(
                    manager.signer.sign(session_id)
                ).decode("utf-8")
            },
        )
        assert on_valid_cookie_mock.called is True


@pytest.mark.asyncio
async def test_handling_invalid_cookie(
    session_id: str, app: FastAPI, settings: SessionSettings
):
    """
    Check that a session middleware handles a request with an invalid cookie
    """

    on_invalid_cookie_mock = AsyncMock(
        return_value=Response(status_code=status.HTTP_400_BAD_REQUEST)
    )
    secret_key = secrets.token_urlsafe(32)
    manager = SessionManager(
        secret_key=secret_key,
        settings=settings,
        on_missing_session=AsyncMock(
            side_effect=HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        ),
    )
    app.add_middleware(
        SessionMiddleware,
        manager=manager,
        on_load_cookie=AsyncMock(return_value=secret_key),
        on_invalid_cookie=on_invalid_cookie_mock,
    )
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        response = await client.get(
            "/",
            cookies={settings.SESSION_COOKIE: session_id},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert on_invalid_cookie_mock.called is True


@pytest.mark.asyncio
async def test_ignoring_invalid_cookie(
    session_id: str, app: FastAPI, settings: SessionSettings
):
    """
    Check that a session middleware ignores a request with an invalid cookie
    """

    async def index(response: Response) -> Response:
        response.status_code = status.HTTP_200_OK
        return response

    secret_key = secrets.token_urlsafe(32)
    session = SessionManager(
        secret_key=secret_key,
        settings=settings,
        on_missing_session=AsyncMock(
            side_effect=HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        ),
    )
    app.add_middleware(
        SessionMiddleware,
        manager=session,
        on_load_cookie=AsyncMock(return_value=secret_key),
    )

    app.add_api_route("/", index)

    async with AsyncClient(app=app, base_url="http://testserver") as client:
        response = await client.get(
            "/",
            cookies={
                # Generate an invalid session id in cookies
                # in order to produce an error
                settings.SESSION_COOKIE: session_id
            },
        )
        assert response.status_code == status.HTTP_200_OK
