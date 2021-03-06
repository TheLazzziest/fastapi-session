from fastapi_session import (
    AsyncSession,
    RedisBackend,
)


def test_create_redis_backend(redis_session: AsyncSession):
    assert isinstance(redis_session._backend, RedisBackend)
