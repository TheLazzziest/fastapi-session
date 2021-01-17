import asyncio
import pytest
import secrets
import uuid

from asynctempfile import NamedTemporaryFile
from flaskapi_session import (
    AsyncSession,
    FSBackend,
    FS_BACKEND_TYPE,
)


@pytest.mark.asyncio
async def test_create_fs_backend(
    session_source: NamedTemporaryFile, event_loop: asyncio.AbstractEventLoop
):
    session = await AsyncSession.create(
        FS_BACKEND_TYPE,
        secrets.token_urlsafe(32),
        uuid.uuid4(),
        backend_kwargs={
            "adapter": session_source.name.split("/").pop(),
        },
        loop=event_loop,
    )

    assert isinstance(session.backend, FSBackend)
