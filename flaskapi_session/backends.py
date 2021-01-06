import asyncio
import pickle
import os
import typing
import tempfile
from collections import defaultdict
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path

import portalocker
import aiofiles

from .interfaces import SessionInterface


@dataclass(eq=False, frozen=False)
class FileSystemInterface(SessionInterface):
    """Session backend based on filesystem storage."""

    session_key: str
    path: str = field(repr=False)
    loop: typing.Optional[asyncio.AbstractEventLoop] = field(repr=False)

    @classmethod
    async def create(
        cls,
        session_key: str,
        path: typing.Optional[Path] = tempfile.gettempdir(),
        loop: typing.Optional[asyncio.AbstractEventLoop] = None,
    ) -> "FileSystemInterface":
        """A factory method for creating and initializing the backend."""
        self = cls(session_key, path, loop)
        if os.path.getsize(self.__source) > 0:
            await self.load()
        return self

    def __init__(
        self,
        session_key: str,
        path: typing.Optional[Path] = tempfile.gettempdir(),
        loop: typing.Optional[asyncio.AbstractEventLoop] = None,
    ):
        """
        :param session_key: Session key defining a path to data
        :param data_path: A basepath to data
        :param loop: An instance of even loop
        """
        self.session_key = session_key
        self.__source = "{0}/{1}".format(path, session_key)
        self.__loop = loop if loop else asyncio.get_running_loop()
        self.__data = defaultdict(None)

    async def load(self) -> None:
        """Load serialized session data from a session data source."""
        self.__data = await asyncio.wait_for(
            self.__loop.run_in_executor(None, self.__load),
            timeout=None,
        )

    def __load(self) -> typing.Dict[str, typing.Any]:
        """Load and unpickle session data from a file."""
        with portalocker.Lock(self.__source, "rb", flags=portalocker.LOCK_EX) as fp:
            return pickle.load(fp)

    async def save(self):
        """Serialize session data to a file."""
        await asyncio.wait_for(
            self.__loop.run_in_executor(None, self.__save),
            timeout=None,
        )

    def __save(self) -> None:
        """Save session data to a file."""
        with portalocker.Lock(self.__source, "wb", flags=portalocker.LOCK_EX) as fp:
            pickle.dump(obj=self.__data, file=fp)

    async def items(self) -> typing.Sequence[typing.Tuple[str, typing.Any]]:
        return self.__data.items()

    async def clear(self) -> None:
        """Clear session storage."""
        self.__data.clear()

    async def keys(self) -> typing.Sequence[str]:
        return self.__data.keys()

    async def values(self) -> typing.Sequence[typing.Any]:
        return self.__data.values()

    async def delete(self, key: str):
        del self.__data[key]

    async def contains(self, item: typing.Any) -> bool:
        return item in self.__data.values()

    async def get(
        self, key: str, default: typing.Optional[typing.Any] = None
    ) -> typing.Any:
        return self.__data.get(key, default)

    async def add(self, key: str, value: typing.Any):
        self.__data[key] = value

    async def update(self, mapping: typing.Dict):
        self.__data.update(mapping)

    async def len(self) -> int:
        return self.__len__()

    async def __aiter__(self):
        return self.__data.items()

    async def __anext__(self):
        raise StopAsyncIteration

    async def asend(self):
        raise NotImplementedError

    async def athrow(self):
        raise NotImplementedError

    async def aclose(self):
        raise NotImplementedError

    def __getitem__(self, name: str) -> typing.Any:
        return self.__data[name]

    def __iter__(self):
        return self.__data.keys()

    def __contains__(self, key: str) -> bool:
        """Look up key entry in the storage."""
        try:
            self.__data[key]
        except KeyError:
            return False
        else:
            return True

    def __len__(self) -> int:
        return len(self.__data.keys())

    def __str__(self) -> str:
        return self.__data_path
