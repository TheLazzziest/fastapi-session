import asyncio
import pickle
import os
import typing
import tempfile
from collections import defaultdict
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path


from ._mixins import FileStorageMixin, DisableMethodsMixin
from .interfaces import BackendInterface


__all__ = ("FSBackend",)


@dataclass(order=False, eq=False, repr=False)
class FSBackend(FileStorageMixin, DisableMethodsMixin, BackendInterface):
    """
    A backend for managing filesystem based session storage.
    """

    session_id: str
    loop: typing.Optional[asyncio.AbstractEventLoop] = field(default=None)

    @classmethod
    async def create(
        cls,
        adapter: typing.Optional[typing.Any] = None,
        loop: typing.Optional[asyncio.AbstractEventLoop] = None,
    ) -> "FSBackend":
        """A factory method for creating and initializing the backend.
        :param adatper: A path to the user session file
        :param loop: A running event loop
        """
        self = cls(adapter, loop)
        if os.path.getsize(self.source) > 0:
            await self.load()
        return self

    def __init__(
        self,
        session_id: str,
        loop: typing.Optional[asyncio.AbstractEventLoop] = None,
    ):
        """
        :param session_key: Session key defining a path to data
        :param loop: An instance of even loop
        """
        super().__init__(session_id)

        self._loop = loop if loop else asyncio.get_running_loop()
        # Initialize the data storage for uploading data from a session data source
        self._data = defaultdict(None)

    @property
    def data(self) -> typing.Dict[str, typing.Any]:
        return self._data

    @data.setter
    def data(self, value: typing.Any) -> None:
        raise NotImplementedError("Modification of the internal storage is forbidden")

    async def load(self) -> None:
        """Load session data from the storage source."""
        self._data = await super().load()

    async def clear(self, pattern: str) -> None:
        """Clear session storage."""
        self._data.clear()

    async def keys(self, pattern: str) -> typing.Sequence[str]:
        return self._data.keys()

    async def delete(self, key: str):
        del self._data[key]

    async def exists(self, *keys: typing.Sequence[str]) -> int:
        return len(set(keys) & set(self._data.keys()))

    async def get(
        self,
        *keys: typing.Sequence[str],
    ) -> typing.Sequence[typing.Any]:
        """Get values by the passed keys from a storage."""
        return [self._data.get(key, None) for key in keys]

    async def set(self, key: str, value: typing.Any, **kwargs) -> None:
        self._data[key] = value

    async def update(self, mapping: typing.Dict, **kwargs) -> None:
        self._data.update(mapping)

    async def len(self, pattern: str) -> int:
        return self.__len__()

    def __getitem__(self, name: str) -> typing.Any:
        return self._data[name]

    def __iter__(self):
        return self._data.keys()

    def __contains__(self, key: str) -> bool:
        """Look up key entry in the storage."""
        try:
            self._data[key]
        except KeyError:
            return False
        else:
            return True

    def __len__(self) -> int:
        return len(self._data.keys())
