import asyncio
import typing

from abc import ABC, abstractmethod
from collections.abc import (
    AsyncGenerator,
    Mapping,
)

__all__ = (
    "BackendInterface",
    "FactoryInterface",
)


class BackendInterface(Mapping, ABC):
    """An abstract interface for a session backend."""

    @abstractmethod
    async def clear(self, pattern: str):
        """Flush a user session data."""
        raise NotImplementedError

    @abstractmethod
    async def keys(
        self, pattern: typing.Optional[str] = None, **kwargs
    ) -> typing.List[str]:
        """Retrieve a list of all keys of a user session."""
        raise NotImplementedError

    @abstractmethod
    async def exists(self, *keys: typing.Sequence[str]) -> typing.Union[int, bool]:
        """Check whether a key is present in a storage."""
        raise NotImplementedError

    @abstractmethod
    async def len(self, pattern: str) -> int:
        """Get a size of key pool of a storage.
        :param pattern: A key namespace for searching.
        """
        raise NotImplementedError

    @abstractmethod
    async def get(self, *keys: typing.Sequence[str]) -> typing.Sequence[typing.Any]:
        """Get the value by the key from a storage."""
        raise NotImplementedError

    @abstractmethod
    async def set(self, key: bytes, value: typing.Any, **kwargs) -> typing.Any:
        """Add a key and its associated value to a storage."""
        raise NotImplementedError

    @abstractmethod
    async def update(self, data: typing.Dict, **kwargs) -> typing.Any:
        """Bulk update of a storage with a passed data."""
        raise NotImplementedError

    @abstractmethod
    async def delete(self, *keys: typing.Sequence[str]) -> typing.Any:
        """Remove a key and its associated value from a storage."""
        raise NotImplementedError


class FactoryInterface(ABC):
    """An interface for adding an abstract factory method in order to instantiate a backend."""

    @classmethod
    async def create(
        cls,
        adapter: typing.Optional[typing.Any],
        loop: typing.Optional[asyncio.AbstractEventLoop] = None,
    ) -> BackendInterface:
        raise NotImplementedError
