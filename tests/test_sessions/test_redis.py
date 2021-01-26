import asyncio
import pytest
import uuid
import secrets

from aioredis import RedisConnection
from fastapi_session import (
    AsyncSession,
    RedisBackend,
    REDIS_BACKEND_TYPE,
)


@pytest.mark.asyncio
async def test_create_redis_backend(
    event_loop: asyncio.AbstractEventLoop, redis_connection: RedisConnection
):
    session = await AsyncSession.create(
        secrets.token_urlsafe(32),
        str(uuid.uuid4()),
        REDIS_BACKEND_TYPE,
        backend_kwargs={
            "adapter": redis_connection,
        },
        loop=event_loop,
    )

    assert isinstance(session.backend, RedisBackend)
