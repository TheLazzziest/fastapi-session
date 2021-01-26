import typing
import secrets
from hashlib import sha256
from unittest import mock
from uuid import uuid4

import pytest

from itsdangerous import BadTimeSignature, SignatureExpired
from fastapi import FastAPI, Request, Response, status
from fastapi_session import (
    SessionManager,
    SessionSettings,
    SessionMiddleware,
)
from pytest_mock import MockerFixture
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_handling_invalid_cookie(
    app: FastAPI, settings: SessionSettings, mocker: MockerFixture
):
    """
    Check that a session middleware handles the case
    when an invalid cookie has been passed
    """

    async def session_id_loader(cookie: str) -> str:
        return cookie

    secret_key = secrets.token_urlsafe(32)
    mocked_handler = mock.MagicMock(
        return_value=Response(status_code=status.HTTP_400_BAD_REQUEST)
    )
    session = SessionManager(
        secret_key=secret_key,
        settings=settings,
        session_id_loader=session_id_loader,
    )
    app.add_middleware(
        SessionMiddleware,
        manager=session,
        on_invalid_cookie=mocked_handler,
    )
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        response = await client.get(
            "/",
            cookies={
                settings.SESSION_COOKIE: sha256(
                    f"{secret_key}:{uuid4()}".encode("utf-8")
                ).hexdigest()
            },
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert mocked_handler.called is True


@pytest.mark.asyncio
async def test_ignoring_invalid_cookie(app: FastAPI, settings: SessionSettings):
    """
    Check that a session middleware ignores the case
    when an invalid cookie has been passed
    """

    async def session_id_loader(cookie: str) -> str:
        # won't be called
        return cookie

    async def index(response: Response) -> Response:
        response.status_code = status.HTTP_200_OK
        return response

    secret_key = secrets.token_urlsafe(32)
    session = SessionManager(
        secret_key=secret_key,
        settings=settings,
        session_id_loader=session_id_loader,
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
                # Generate an invalid session id in cookies
                # in order to produce an error
                settings.SESSION_COOKIE: sha256(
                    f"{secret_key}:{uuid4()}".encode("utf-8")
                ).hexdigest()
            },
        )
        assert response.status_code == status.HTTP_200_OK
