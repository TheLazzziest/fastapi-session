import asyncio
import pytest
import secrets
import uuid

from asynctempfile import NamedTemporaryFile
from fastapi_session import (
    AsyncSession,
    FSBackend,
    FS_BACKEND_TYPE,
)


@pytest.mark.asyncio
async def test_create_fs_backend(fs_session: AsyncSession):
    assert isinstance(fs_session.backend, FSBackend)
