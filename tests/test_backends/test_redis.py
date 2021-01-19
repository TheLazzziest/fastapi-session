import pickle
import pytest
import uuid
import typing

from fastapi_session.backends import RedisBackend


@pytest.mark.asyncio
async def test_get_by_key_under_namespace(
    session_id: uuid.UUID, redis_backend: RedisBackend
):
    """Check whether a key is under a namespace."""
    key, value = f"{session_id}:fastapi_session", "cool"
    await redis_backend.set(key, value)
    keys = [key.decode("utf-8") for key in await redis_backend.keys(f"{session_id}*")]
    assert key in keys


@pytest.mark.asyncio
async def test_set_by_key_under_namespace(
    session_id: uuid.UUID, redis_backend: RedisBackend
):
    """Check that a value is to be set for a key under a namespace."""
    key, value = f"{session_id}:fastapi_session", "fast"
    await redis_backend.set(key, value)
    values = [value.decode("utf-8") for value in await redis_backend.get(key)]
    assert value in values


@pytest.mark.asyncio
async def test_delete_by_key_under_namespace(redis_backend: RedisBackend):
    """Check that a value is to be removed by a key under a namespace."""
    key, value = "key", "to-delete"
    await redis_backend.set(key, value)
    await redis_backend.delete(key)
    assert await redis_backend.exists(key) == False


@pytest.mark.asyncio
async def test_bulk_update(
    session_id: uuid.UUID,
    session_data: typing.Dict[str, typing.Any],
    redis_backend: RedisBackend,
):
    def serialize_data(
        items: typing.Tuple[str, typing.Any]
    ) -> typing.Tuple[str, typing.Any]:
        key, value = items
        return (f"{session_id}:{key}", pickle.dumps(value))

    """Test applying of bulk update in redis storage."""
    session_data_keys = session_data.keys()
    data_size = len(session_data_keys)
    backend_data_key_subset = list(session_data_keys)[: (data_size // 2)]
    # Build a data payload for testing
    data = {}
    for key in backend_data_key_subset:
        data[key] = session_data[key]
    # Apply the data to the redis storage
    serialized_data = dict(map(serialize_data, data.items()))
    await redis_backend.update(serialized_data)
    # Validate that all entries have been applied
    RAW_KEY_INDEX_PART = 1
    raw_backend_saved_keys = [
        key.decode("utf-8").split(f"{session_id}:").pop()
        for key in await redis_backend.keys(f"{session_id}*")
    ]
    assert (set(backend_data_key_subset) - set(raw_backend_saved_keys)) == set()


@pytest.mark.asyncio
async def test_clear_session(session_id: uuid.UUID, redis_backend: RedisBackend):
    # Initialize an empty session
    key, value = f"{session_id}:fast", "api"
    await redis_backend.set(key, value)

    # Check that the session has some values
    assert len(await redis_backend.keys(f"{session_id}*")) == 1

    # Flush the session
    await redis_backend.clear(f"{session_id}*")

    # Check that the session has been flushed
    assert len(await redis_backend.keys(f"{session_id}*")) == 0
