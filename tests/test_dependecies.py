import typing
import secrets
from base64 import b64encode
from unittest.mock import AsyncMock

import pytest
from cryptography.fernet import Fernet
from fastapi import Depends, FastAPI, Request, Response, HTTPException, status
from fastapi_session import (
    AsyncSession,
    decrypt_session,
    encrypt_session,
    get_user_session,
    SessionManager,
    SessionSettings,
    SessionMiddleware,
)
from httpx import AsyncClient
from pytest_mock import MockerFixture


@pytest.mark.asyncio
async def test_user_session_dependency(
    secret: str,
    signer: typing.Type[Fernet],
    session_id: str,
    app: FastAPI,
    settings: SessionSettings,
):
    """
    Check that a user session will be injected as a dependency.
    """

    async def index(session: AsyncSession = Depends(get_user_session)) -> Response:
        await session.set("test", "passed")
        await session.save()
        return Response(status_code=status.HTTP_200_OK)

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
        on_load_cookie=AsyncMock(return_value=session_id),
        on_invalid_cookie=AsyncMock(
            return_value=Response(status_code=status.HTTP_401_UNAUTHORIZED)
        ),
    )
    app.state.session = manager
    app.add_api_route("/", index)
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        response = await client.get(
            "/",
            cookies={settings.COOKIE_NAME: encrypt_session(signer, session_id)},
        )
        session = await manager.load_session(session_id)
        assert response.status_code == status.HTTP_200_OK
        assert list(await session.get("test")).pop() == "passed"


@pytest.mark.asyncio
async def test_missing_user_session_dependency(
    secret: str,
    signer: typing.Type[Fernet],
    session_id: str,
    app: FastAPI,
    settings: SessionSettings,
):
    """
    Check that a user session will be injected as a dependency.
    """

    async def index(session: AsyncSession = Depends(get_user_session)) -> Response:
        return Response(status_code=status.HTTP_200_OK)

    on_missing_session_mock = AsyncMock(
        side_effect=HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    )
    manager = SessionManager(
        secret=secret,
        signer=signer,
        settings=settings,
        on_missing_session=on_missing_session_mock,
    )
    app.add_middleware(
        SessionMiddleware,
        manager=manager,
        on_load_cookie=AsyncMock(return_value=secrets.token_urlsafe(8)),
    )
    app.state.session = manager
    app.add_api_route("/", index)
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        response = await client.get(
            "/",
            # Generate an invalid session cookie
            # also disable a callback for an invalid cookie
            # in order to trigger a callback on missing a user session
            cookies={settings.COOKIE_NAME: session_id},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert on_missing_session_mock.called is True
