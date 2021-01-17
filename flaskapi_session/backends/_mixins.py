import asyncio
import pickle
import tempfile
import typing
from abc import ABC, abstractmethod
from functools import cached_property, partial
from pathlib import Path

import portalocker


class FileStorageMixin:
    """A mixin for adding capabilities of a file manipulation."""

    def __init__(
        self, session_id: str, storage_path: Path = Path(tempfile.gettempdir())
    ):
        """
        :param session_id: An id of a user session
        :param storage_path: A base path to session data source files
        """
        self.session_id = session_id
        self.storage_path = storage_path
        self.storage_path.mkdir(exist_ok=True)

    @cached_property
    def source(self) -> Path:
        """Generate an absolute path to the session data source file."""
        source_path = self.storage_path.joinpath(self.session_id)
        source_path.touch(exist_ok=True)
        return source_path

    async def load(self) -> typing.Dict[str, typing.Any]:
        """Load serialized session data from a session data source."""
        return await asyncio.wait_for(
            self._loop.run_in_executor(None, self.__load),
            timeout=None,
        )

    def __load(self) -> typing.Dict[str, typing.Any]:
        """Load and unpickle session data from a file."""
        with portalocker.Lock(self.source, "rb", flags=portalocker.LOCK_EX) as fp:
            return pickle.load(fp)

    async def save(self, data: typing.Dict[str, typing.Any]):
        """Serialize session data to a file."""
        await asyncio.wait_for(
            self._loop.run_in_executor(None, partial(self.__save, data=data)),
            timeout=None,
        )

    def __save(self, data: typing.Dict[str, typing.Any]) -> None:
        """Save session data to a file."""
        with portalocker.Lock(self.source, "wb", flags=portalocker.LOCK_EX) as fp:
            pickle.dump(obj=self._data, file=fp)


class DisableMethodsMixin:
    """A mixin for disabling some python magic methods."""

    def __getitem__(self, key):
        """Disabled method for accessing an item using an index."""
        raise NotImplementedError

    def __iter__(self):
        """Disabled method for iteration."""
        raise NotImplementedError

    def __len__(self):
        """Disabled method for getting the length of the container."""
        raise NotImplementedError

    def __eq__(self):
        """Disable the equality method"""
        raise NotImplementedError

    def __ne__(self):
        """Disable the negation of equality method"""
        raise NotImplementedError

    def __len__(self):
        """Disable getting the size of the container"""
        raise NotImplementedError
