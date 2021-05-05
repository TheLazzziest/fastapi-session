import asyncio
import os
import pickle
import pytest
import secrets
import string
import typing
from hashlib import sha256
from datetime import timedelta
from uuid import uuid4, UUID
from pathlib import Path
from functools import partial
from string import ascii_letters, printable

import pendulum
from aioredis import Redis, create_redis_pool
from asgi_lifespan import LifespanManager
from asynctempfile import NamedTemporaryFile
from cryptography.fernet import Fernet
from fastapi import FastAPI
from fastapi_session import (
    AES_SIV_Encryptor,
    AsyncSession,
    create_backend,
    create_namespace,
    FS_BACKEND_TYPE,
    FSBackend,
    encrypt_session,
    get_session_settings,
    REDIS_BACKEND_TYPE,
    RedisBackend,
    SessionSettings,
)

from .factories import generate_session_data


@pytest.fixture(scope="session")
def secret() -> str:
    return "3xmPiROFJO2Kj4lu-UNQ5ap-5XsxOyv1LGep2xTp1L8="


@pytest.fixture(scope="session")
def session_id() -> str:
    """Generate session id for a backend."""
    return "6428b4c1-c360-4605-9318-ed99371b7bd6"


@pytest.fixture(scope="session")
def signer(secret: str) -> typing.Type[Fernet]:
    return Fernet(secret.encode("utf-8"))


@pytest.fixture(scope="session")
def salt(secret: str) -> str:
    """A PBKDF salt."""
    return sha256(secret.encode("utf-8")).hexdigest()


@pytest.fixture(scope="session")
def encryptor(secret: str, salt: str) -> AES_SIV_Encryptor:
    return AES_SIV_Encryptor(secret, salt)


@pytest.fixture(scope="session")
def token(session_id: str, signer: typing.Type[Fernet]) -> bytes:
    """Generate an encrypted token based on a session id."""
    return encrypt_session(
        signer, session_id, pendulum.now().subtract(minutes=10)
    )  # token is expired in 10 minutes


@pytest.fixture(scope="function")
async def session_data() -> typing.Dict[str, typing.Any]:
    """Create a predefined session data."""
    return generate_session_data()


@pytest.fixture(scope="function")
def settings() -> SessionSettings:
    return get_session_settings()


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
) -> typing.Generator[Redis, None, None]:
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
    redis_connection: Redis,
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
    session_id: typing.Hashable,
    settings: SessionSettings,
    encryptor: AES_SIV_Encryptor,
    session_source: NamedTemporaryFile,
    event_loop: asyncio.AbstractEventLoop,
) -> typing.Generator[AsyncSession, None, None]:
    session = await AsyncSession.create(
        encryptor=encryptor,
        namespace=create_namespace(encryptor=encryptor, session_id=session_id),
        backend=await create_backend(
            FS_BACKEND_TYPE,
            adapter=session_source.name.split("/").pop(),
            loop=event_loop,
        ),
        loop=event_loop,
    )
    yield session
    await session.clear()


@pytest.fixture(scope="function")
async def redis_session(
    session_id: typing.Hashable,
    settings: SessionSettings,
    encryptor: AES_SIV_Encryptor,
    event_loop: asyncio.AbstractEventLoop,
    redis_connection: Redis,
) -> typing.Generator[AsyncSession, None, None]:
    session = await AsyncSession.create(
        encryptor=encryptor,
        namespace=create_namespace(encryptor=encryptor, session_id=session_id),
        backend=await create_backend(REDIS_BACKEND_TYPE, adapter=redis_connection),
        loop=event_loop,
    )
    yield session
    await session.clear()


@pytest.fixture(scope="function")
async def app() -> typing.Generator[FastAPI, None, None]:
    app = FastAPI()
    async with LifespanManager(app):
        yield app
