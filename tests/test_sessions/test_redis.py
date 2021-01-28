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
async def test_create_redis_backend(redis_session: AsyncSession):
    assert isinstance(redis_session.backend, RedisBackend)
