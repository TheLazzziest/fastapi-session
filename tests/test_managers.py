import pytest
import secrets
import typing

from fastapi_session import (
    AsyncSession,
    REDIS_BACKEND_TYPE,
    SessionManager,
    SessionSettings,
    AsyncSession,
)
from aioredis import Redis, create_redis_pool


@pytest.mark.asyncio
async def test_load_redis_session_backend(
    settings: SessionSettings,
    redis_connection: Redis,
):
    async def loader(cookie: str) -> str:
        return cookie

    settings.SESSION_BACKEND = REDIS_BACKEND_TYPE
    manager = SessionManager(
        secret_key=secrets.token_urlsafe(32),
        settings=settings,
        session_id_loader=loader,
        backend_adapter=redis_connection,
    )

    session = await manager.load_session(secrets.token_urlsafe(8))

    assert isinstance(session, AsyncSession)
    assert isinstance(session.backend.adapter, Redis)
