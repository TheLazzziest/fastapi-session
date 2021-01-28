import asyncio
import typing
import pickle
from importlib import import_module
from itsdangerous import TimestampSigner
from hashlib import sha256

from .backends import BackendInterface

__all__ = ("AsyncSession",)


class AsyncFileSessionMixin:
    """A mixin for adding some helper methods for managin filesystem session storage."""

    async def save(self) -> None:
        """Save the state of the session to a storage file."""
        await self.backend.save()

    async def load(self) -> None:
        """Load the session from a saved storage file."""
        await self.backend.load()


class AsyncSession(AsyncFileSessionMixin):
    """
    A backend template representing an abstract methods for managing a particular session storage.
    """

    def __init__(
        self,
        secret_key: str,
        session_id: str,
        backend: BackendInterface,
        loop: typing.Optional[asyncio.AbstractEventLoop] = None,
    ):
        """
        :param str secret_key: An application secret key
        :param str session_id: A user session id
        :param BackendInterface backend: An instance of a session backend
        """
        self.namespace = sha256(
            f"{secret_key}:{session_id}".encode("utf-8")
        ).hexdigest()
        self.backend = backend
        self.loop = loop if loop else asyncio.get_running_loop()

    @classmethod
    async def create(
        cls,
        secret_key: str,
        session_id: str,
        backend: str,
        backend_kwargs: typing.Dict[str, typing.Any],
        loop: typing.Optional[asyncio.AbstractEventLoop] = None,
    ) -> "AsyncSession":
        """A method for instantiating a session storage backend.

        :param str secret_key: An application secret key
        :param str session_id: A user session id
        :param str backend: An absolute path to session id
        :param dict backend_kwargs: Session backend parameters
        :param AbstractEventLoop loop: An instance of the running event loop
        """
        backend: typing.Optional[BackendInterface] = cls.load_backend(backend)
        if backend is None:
            raise ValueError(f"Undefined backend type: {backend}")
        backend_instance = await backend.create(**backend_kwargs, loop=loop)
        return cls(secret_key, session_id, backend_instance, loop=loop)

    @staticmethod
    def load_backend(backend_path: str) -> typing.Optional[BackendInterface]:
        parts = backend_path.split(".")
        module_path = ".".join(parts[0:-1])
        module = import_module(module_path)
        return getattr(module, parts[-1], None)

    async def clear(self):
        return await self.backend.clear(f"{self.namespace}*")

    async def keys(self) -> typing.List[str]:
        """Retrieve a list of all keys placed in a storage."""
        return await self.backend.keys(f"{self.namespace}*")

    async def exists(self, *keys: typing.Sequence[str]) -> int:
        """Check whether keys is present in a storage."""
        return await self.backend.exists(
            *map(
                lambda key: f"{self.namespace}{sha256(key.encode('utf-8')).hexdigest()}",
                keys,
            )
        )

    async def len(self) -> int:
        """Get the size of a storage key pool."""
        return await self.backend.len(self.namespace)

    async def get(self, *keys: typing.Sequence[str]) -> typing.Any:
        """Get the values by the keys from a storage."""
        return map(
            lambda value: pickle.loads(value) if value else None,
            await self.backend.get(
                *map(
                    lambda key: f"{self.namespace}{sha256(key.encode('utf-8')).hexdigest()}",
                    keys,
                ),
            ),
        )

    async def set(self, key: str, value: typing.Any, **kwargs) -> typing.Any:
        """Add a key and its associated value to a storage."""
        return await self.backend.set(
            f"{self.namespace}{sha256(key.encode('utf-8')).hexdigest()}",
            pickle.dumps(value),
            **kwargs,
        )

    async def update(self, data: typing.Dict, **kwargs) -> None:
        """Bulk update of a storage with a passed data."""
        return await self.backend.update(
            map(
                lambda key, value: (
                    f"{self.namespace}{sha256(key.encode('utf-8')).hexdigest()}",
                    pickle.dumps(value),
                ),
                data.items(),
            ),
            **kwargs,
        )

    async def delete(self, *keys: typing.Sequence[str]) -> str:
        """Remove keys and its associated value from a storage."""
        return await self.backend.delete(
            *map(
                lambda key: f"{self.namespace}{sha256(key.encode('utf-8')).hexdigest()}",
                keys,
            )
        )
