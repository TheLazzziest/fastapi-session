import asyncio
import os
import pickle
import pytest
import string
import typing
from pathlib import Path
from functools import partial
from string import ascii_letters, printable

from asynctempfile import TemporaryDirectory, NamedTemporaryFile

from flaskapi_session.backends import FileSystemInterface

from .factories import generate_session_data


@pytest.fixture(scope="function")
async def session_data() -> typing.Dict[str, typing.Any]:
    """Create a predefined session data."""
    return generate_session_data()


@pytest.fixture(scope="function")
async def session_source(
    event_loop: asyncio.AbstractEventLoop, session_data: typing.Dict[str, typing.Any]
) -> typing.Generator[NamedTemporaryFile, None, None]:
    """Create a predefined session data source."""
    async with TemporaryDirectory() as data_path:
        async with NamedTemporaryFile(prefix=f"{data_path}/") as session_file:
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
) -> typing.Generator[FileSystemInterface, None, None]:
    """Create a session backend based on filesystem storage."""
    path = Path(session_source.name)
    yield await FileSystemInterface.create(path.name, str(path.parent))
