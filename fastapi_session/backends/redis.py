import asyncio
import pickle
import typing
from aioredis import RedisConnection
from dataclasses import dataclass, field
from itertools import chain

from ._mixins import DisableMethodsMixin
from .interfaces import BackendInterface, FactoryInterface


__all__ = ("RedisBackend",)


@dataclass(order=False, eq=False, repr=False)
class RedisBackend(DisableMethodsMixin, FactoryInterface, BackendInterface):
    """
    A backend for managing redis based session storage.
    """

    adapter: RedisConnection
    loop: typing.Optional[asyncio.AbstractEventLoop] = field(default=None)

    @classmethod
    async def create(
        cls,
        adapter: RedisConnection,
        loop: typing.Optional[asyncio.AbstractEventLoop] = None,
    ) -> "RedisBackend":
        """
        A factory method for creating and initializing the backend.

        :param adapter: An opened connection to a redis server
        :param loop: An instance of event loop
        """
        return cls(adapter, loop)

    async def clear(self, namespace: str) -> None:
        keys = await self.keys(namespace)
        if len(keys) > 0:
            await self.adapter.delete(*keys)

    async def keys(self, namespace: str) -> typing.List[str]:
        return [
            key.decode("utf-8") for key in await self.adapter.keys(f"{namespace}:*")
        ]

    async def exists(self, *key: typing.Sequence[str]) -> int:
        return await self.adapter.exists(*key)

    async def len(self, namespace: str) -> int:
        return len(await self.adapter.keys(namespace))

    async def get(
        self,
        *keys: typing.Sequence[str],
    ) -> typing.Sequence[typing.Any]:
        """Get values by the passed keys from a storage."""
        return [key.decode("utf-8") for key in await self.adapter.mget(*keys)]

    async def set(self, key: str, value: typing.Any, **kwargs) -> None:
        """Set the value to the key in a storage."""
        return await self.adapter.set(key, value, **kwargs)

    async def update(self, mapping: typing.Dict[str, typing.Any], **kwargs) -> None:
        """Update a storage with the passed mapping."""
        return await self.adapter.mset(*chain.from_iterable(mapping.items()))

    async def delete(self, *keys: typing.Sequence[str]) -> str:
        return await self.adapter.delete(*keys)
