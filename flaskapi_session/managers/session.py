import asyncio
from typing import Awaitable, Union, Optional

from fastapi import FastAPI, Request, Response

from ..settings import (
    DATABASE_BACKEND_TYPE,
    FS_BACKEND_TYPE,
    MEMORY_BACKEND_TYPE,
    REDIS_BACKEND_TYPE,
)
from ..session import AsyncSession

from .cookie import CookieManager


class SessionManager:
    """Session manager to use session storage system."""

    def __init__(
        self,
        secret_key: str,
        backend_type: Union[
            DATABASE_BACKEND_TYPE,
            FS_BACKEND_TYPE,
            MEMORY_BACKEND_TYPE,
            REDIS_BACKEND_TYPE,
        ],
        session_id_loader: Awaitable,
        backend_adapter_loader: Optional[Awaitable] = None,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ):
        """
        :param session_id_name: A name(key) for session id for storing on client side
        :param session_id_loader: A function(coroutine) for loading session_data
        :param backend_type: A type of backend for managing a session storage
        :param backend_adapter_loader: A function(coroutine) for loading adapter
        """
        # Session storage settings
        self._secret_key = secret_key
        self._backend_type = backend_type
        self._adapter_loader = backend_adapter_loader
        # Delegators for managing a session id on a developer side
        self._session_id_loader = session_id_loader
        # A running event loop
        self._loop = loop

    async def load_session(self, app: FastAPI, cookie: str) -> AsyncSession:
        """A factory method for loading a session storage."""
        session_id: str = await self._session_id_loader(cookie)
        return await AsyncSession.create(
            self._backend_type,
            self._secret_key,
            session_id,
            backend_kwargs={
                # If a backend is of filesystem type
                # then a session id can be used
                # as a source of a session file as an example
                "adapter": (
                    await self._adapter_loader(app)
                    if self._adapter_loader
                    else session_id
                ),
            },
            loop=self._loop,
        )
