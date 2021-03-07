import asyncio
import json
import pickle
import typing
from functools import cached_property

from cryptography.fernet import Fernet
from functools import partial
from hashlib import sha256

from .backends import BackendInterface
from .encryptors import EncryptorInterface
from .utils import import_backend

__all__ = ("AsyncSession",)


class AsyncFileSessionMixin:
    """A mixin for adding some helper methods for managin filesystem session storage."""

    async def save(self) -> None:
        """Save the state of the session to a storage file."""
        await self._backend.save()

    async def load(self) -> None:
        """Load the session from a saved storage file."""
        await self._backend.load()


class AsyncSession(AsyncFileSessionMixin):
    """
    A backend template representing an abstract methods for managing a particular session storage.
    """

    def __init__(
        self,
        namespace: str,
        encryptor: typing.Type[EncryptorInterface],
        backend: typing.Type[BackendInterface],
        loop: typing.Optional[asyncio.AbstractEventLoop] = None,
    ):
        """
        :param str namespace: A user session namespace
        :param callable encryptor: A callable object for session data encryption
        :param BackendInterface backend: An instance of a session backend
        """
        self._namespace = namespace
        self._encryptor = encryptor
        self._backend = backend
        self._loop = loop if loop else asyncio.get_running_loop()

    @classmethod
    async def create(
        cls,
        namespace: str,
        encryptor: typing.Type[EncryptorInterface],
        backend: typing.Type[BackendInterface],
        loop: typing.Optional[asyncio.AbstractEventLoop] = None,
    ) -> "AsyncSession":
        """A method for instantiating a session storage backend.

        :param str namespace: A user session namespace
        :param BackendInterface backend: An instance of a particular backend
        :param AbstractEventLoop loop: An instance of the running event loop
        """
        return cls(namespace, encryptor, backend, loop)

    async def clear(self):
        return await self._backend.clear(self._namespace)

    async def keys(self) -> typing.List[str]:
        """Retrieve a list of all keys placed in a storage."""
        return await self._backend.keys(self._namespace)

    async def exists(self, *keys: typing.Sequence[str]) -> int:
        """Check whether keys is present in a storage."""
        return await self._backend.exists(
            *map(
                lambda key: f"{self._namespace}:{self._encryptor.encrypt(key)}",
                keys,
            )
        )

    async def len(self) -> int:
        """Get the size of a storage key pool."""
        return await self._backend.len(self._namespace)

    async def get(
        self,
        *keys: typing.Sequence[str],
        loader: typing.Optional[typing.Callable] = json.loads,
    ) -> typing.Any:
        """Get the values by the keys from a storage."""

        return map(
            lambda value: loader(self._encryptor.decrypt(value)) if value else None,
            await self._backend.get(
                *map(
                    lambda key: f"{self._namespace}:{self._encryptor.encrypt(key)}",
                    keys,
                )
            ),
        )

    async def set(
        self,
        key: str,
        value: typing.Any,
        serializer: typing.Optional[typing.Callable] = json.dumps,
        **opts: typing.Mapping[str, typing.Any],
    ) -> typing.Any:
        """Add a key and its associated value to a storage."""
        return await self._backend.set(
            f"{self._namespace}:{self._encryptor.encrypt(key)}",
            self._encryptor.encrypt(serializer(value)),
            **opts,
        )

    async def update(
        self,
        data: typing.Dict,
        serializer: typing.Optional[typing.Callable] = json.dumps,
        **opts,
    ) -> None:
        """Bulk update of a storage with a passed data."""
        return await self._backend.update(
            map(
                lambda key, value: (
                    f"{self._namespace}:{self._encryptor.encrypt(key)}",
                    self._encryptor.encrypt(serializer(value)),
                ),
                data.items(),
            ),
            **opts,
        )

    async def delete(self, *keys: typing.Sequence[str]) -> str:
        """Remove keys and its associated value from a storage."""
        return await self._backend.delete(
            *map(
                lambda key: f"{self._namespace}:{self._encryptor.encrypt(key)}",
                keys,
            )
        )
