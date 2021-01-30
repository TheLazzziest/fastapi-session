import pytest
import secrets
import typing
from unittest.mock import AsyncMock

from fastapi import HTTPException, Request, Response, status
from fastapi_session import (
    AsyncSession,
    create_session_manager,
    FSBackend,
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
