import typing
from abc import ABC, abstractmethod
from collections.abc import (
    Mapping,
    AsyncGenerator,
)


class SessionInterface(ABC, Mapping, AsyncGenerator):
    """An abstract interface for a session backend."""

    @abstractmethod
    async def clear(self):
        raise NotImplementedError

    @abstractmethod
    async def keys(self, key: str) -> typing.List[str]:
        raise NotImplementedError

    @abstractmethod
    async def items(self) -> typing.Sequence[typing.Tuple[str, typing.Any]]:
        raise NotImplementedError

    @abstractmethod
    async def values(self) -> typing.List[typing.Any]:
        raise NotImplementedError

    @abstractmethod
    async def contains(self, item: typing.Any) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def len(self) -> int:
        raise NotImplementedError

    @abstractmethod
    async def get(
        self, key: str, default: typing.Optional[typing.Any] = None
    ) -> typing.Any:
        raise NotImplementedError

    @abstractmethod
    async def add(self, key: str, value: typing.Any):
        raise NotImplementedError

    @abstractmethod
    async def update(self, mapping: typing.Dict):
        raise NotImplementedError

    def __eq__(self):
        raise NotImplementedError

    def __ne__(self):
        raise NotImplementedError


class BackendInterface:
    def get_session(self, key: str) -> SessionInterface:
        pass