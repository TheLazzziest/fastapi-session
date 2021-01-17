"""A set of tests for session storages of different types."""
import asyncio
import pytest
import typing
import sys
import uuid
from pathlib import Path
from concurrent import futures

from flaskapi_session.backends import FSBackend


@pytest.mark.asyncio
async def test_concurrent_access(
    session_data: typing.Dict[str, typing.Any],
    session_source: typing.IO[bytes],
    fs_backend: FSBackend,
    event_loop: asyncio.AbstractEventLoop,
):
    """Test concurrent access of mutltple backends to the same data source."""
    executor = futures.ThreadPoolExecutor(max_workers=2)

    # Prepare new session backend
    path = Path(session_source.name)
    new_fs_backend = await FSBackend.create(path.name, event_loop)

    # Prepare modified session data
    testing_key = list(session_data.keys())[0]
    await new_fs_backend.delete(testing_key)

    # Try to run multiple tasks as quick as possible
    # Configuring a thread execution
    sw_interval = sys.getswitchinterval()
    target_interval = 1e-12
    # Greatly improve the chance of an operation being interrupted
    # by thread switch, thus testing synchronization effectively.
    # Feel free to tweak the parameters below to see their impact.
    # see: https://gist.github.com/mRcfps/0af4f1cb29ffe27cf3aa05d542ac742a
    sys.setswitchinterval(target_interval)
    # Run coroutine functions in two separate threads
    coros = [
        # Try to load unmodified data
        fs_backend.load(),
        # Try to save modified data
        new_fs_backend.save(new_fs_backend.data),
        new_fs_backend.load(),
    ]
    await asyncio.gather(*coros, loop=event_loop)

    # Check concurrent access
    assert testing_key in fs_backend
    assert testing_key not in new_fs_backend

    # Update fs_backend state
    await fs_backend.load()
    assert testing_key not in fs_backend

    sys.setswitchinterval(sw_interval)


@pytest.mark.asyncio
async def test_load_session_data(
    subtests: typing.Any,
    fs_backend: FSBackend,
    session_data: typing.Dict[str, typing.Any],
):
    """Test session storage consistency after deserialization."""
    session_data_keys = session_data.keys()
    data_size = len(session_data_keys)
    backend_data_key_subset = list(session_data_keys)[: (data_size // 2)]
    for key in backend_data_key_subset:
        with subtests.test(msg=f"Checking value by the key:{key}"):
            assert await fs_backend.exists(key) == 1


@pytest.mark.asyncio
async def test_backend_data_key_length(
    session_id: uuid.UUID,
    fs_backend: FSBackend,
    session_data: typing.Dict[str, typing.Any],
):
    """Check correct supporting for len magic  method."""
    keys = session_data.keys()
    keys_length = len(keys)
    assert await fs_backend.len(session_id) == keys_length
    assert len(fs_backend) == keys_length
