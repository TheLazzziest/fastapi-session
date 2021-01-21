import asyncio
import os
import pickle
import pytest
import secrets
import string
import typing
from uuid import uuid4, UUID
from pathlib import Path
from functools import partial
from string import ascii_letters, printable

from aioredis import RedisConnection, create_redis_pool
from asynctempfile import NamedTemporaryFile

from fastapi import FastAPI
from fastapi_session import (
    AsyncSession,
    FS_BACKEND_TYPE,
    FSBackend,
    REDIS_BACKEND_TYPE,
    RedisBackend,
    SessionSettings,
    get_session_settings,
)

from .factories import generate_session_data


@pytest.fixture(scope="session")
def session_id() -> str:
    """Generate session id for a backend."""
    return str(uuid4())


@pytest.fixture(scope="function")
async def session_data() -> typing.Dict[str, typing.Any]:
    """Create a predefined session data."""
    return generate_session_data()


@pytest.fixture(scope="function")
def settings() -> SessionSettings:
    yield get_session_settings()


@pytest.fixture(scope="function")
async def session_source(
    event_loop: asyncio.AbstractEventLoop, session_data: typing.Dict[str, typing.Any]
) -> typing.Generator[NamedTemporaryFile, None, None]:
    """Create a predefined session data source."""
    async with NamedTemporaryFile("wb") as session_file:
        await asyncio.wait_for(
            event_loop.run_in_executor(
                None, partial(pickle.dump, obj=session_data, file=session_file.raw)
            ),
            timeout=None,
        )
        yield session_file


@pytest.fixture(scope="function")
async def fs_backend(
    session_source: NamedTemporaryFile,
    event_loop: asyncio.AbstractEventLoop,
) -> typing.Generator[FSBackend, None, None]:
    """Create an instance of FSBackend for a filesystem storage."""
    path = Path(session_source.name)
    yield await FSBackend.create(path.name, loop=event_loop)


@pytest.fixture(scope="function")
async def redis_connection(
    event_loop: asyncio.AbstractEventLoop,
) -> typing.Generator[RedisConnection, None, None]:
    """Open a connection to Redis database."""
    connection = await create_redis_pool(
        "redis://localhost:6379/1",
        loop=event_loop,
    )
    yield connection
    connection.close()
    await connection.wait_closed()


@pytest.fixture(scope="function")
async def redis_backend(
    redis_connection: RedisConnection,
    session_id: UUID,
    event_loop: asyncio.AbstractEventLoop,
) -> typing.Generator[RedisBackend, None, None]:
    """Create an instance of RedisBackend for redis storage."""
    backend = await RedisBackend.create(adapter=redis_connection, loop=event_loop)
    yield backend
    if await backend.keys(f"{session_id}*"):
        await backend.clear(f"{session_id}*")


@pytest.fixture(scope="function")
async def fs_session(
    session_id: UUID,
    event_loop: asyncio.AbstractEventLoop,
    redis_connection: RedisConnection,
) -> typing.Generator[AsyncSession, None, None]:
    backend = await AsyncSession.create(
        FS_BACKEND_TYPE,
        secrets.token_urlsafe(32),
        session_id,
        backend_kwargs={
            "adapter": redis_connection,
        },
        loop=event_loop,
    )
    yield backend
    await backend.clear(f"{session_id}*")


@pytest.fixture(scope="function")
async def redis_session(
    session_id: UUID,
    event_loop: asyncio.AbstractEventLoop,
    redis_connection: RedisConnection,
) -> typing.Generator[AsyncSession, None, None]:
    yield await AsyncSession.create(
        REDIS_BACKEND_TYPE,
        secrets.token_urlsafe(32),
        session_id,
        backend_kwargs={
            "adapter": redis_connection,
        },
        loop=event_loop,
    )


@pytest.fixture(scope="function")
def app() -> typing.Generator[FastAPI, None, None]:
    yield FastAPI()