import asyncio
import typing
from dataclasses import dataclass, field

from ._mixins import DisableMethodsMixin
from .interfaces import BackendInterface


@dataclass(order=False, eq=False, repr=False)
class DBBackend(DisableMethodsMixin, BackendInterface):
    """A backend for managing database based session storage."""

    adapter: typing.Any
    loop: typing.Optional[asyncio.AbstractEventLoop] = field(default=None)

    @classmethod
    async def create(
        cls,
        adapter: typing.Any,
        loop: typing.Optional[asyncio.AbstractEventLoop] = None,
    ) -> "DBBackend":
        return cls(adapter, loop)