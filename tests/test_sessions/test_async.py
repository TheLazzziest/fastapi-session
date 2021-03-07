from fastapi_session import AsyncSession, FSBackend, RedisBackend


def test_create_fs_backend(fs_session: AsyncSession):
    assert isinstance(fs_session._backend, FSBackend)


def test_create_redis_backend(redis_session: AsyncSession):
    assert isinstance(redis_session._backend, RedisBackend)


# @TODO: Add unit tests for AsyncSession operations
