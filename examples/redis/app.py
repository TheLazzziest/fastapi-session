import logging
import typing
import json
from hashlib import sha256
from uuid import uuid4
from typing import Any, List


from aioredis import create_redis_pool, RedisConnection
from itsdangerous.exc import BadTimeSignature, SignatureExpired
from fastapi import Depends, FastAPI, Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi_session import (
    connect,
    Connection,
    AsyncSession,
    get_session_manager,
    get_user_session,
    SessionManager,
    SessionSettings,
)


logger = logging.getLogger(__name__)

app = FastAPI()
settings = SessionSettings()
secret_key = "aYhzAqkFsyB9ZWlrYaeu8258TqQYdo2_u6MWDVr0HTs"


async def session_id_generator(app: FastAPI) -> str:
    """A delegate for generating of a session id."""
    return sha256(f"{secret_key}:{uuid4()}".encode("utf-8")).hexdigest()


async def on_missing_session(request: Request) -> None:
    """A delegate for restoring of a session id from the passed cookie."""
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


async def on_load_cookie(request: Request, cookie: str) -> str:
    return cookie


async def on_invalid_cookie(
    request: Request, exc: typing.Union[BadTimeSignature, SignatureExpired]
) -> Response:
    response = Response(status_code=status.HTTP_401_UNAUTHORIZED)
    response.delete_cookie(settings.SESSION_COOKIE)
    return response


def on_load_backend_adapter(app: FastAPI) -> Connection:
    return app.state.redis


@app.on_event("startup")
async def open_session():
    conn_pool = await create_redis_pool("redis://localhost:6379/1")
    app.state.redis = conn_pool


@app.on_event("shutdown")
async def close_session():
    conn_pool = app.state.redis
    await conn_pool
    await conn_pool.wait_closed()


connect(
    app=app,
    settings=settings,
    secret_key=secret_key,
    backend_adapter_loader=on_load_backend_adapter,
    on_load_cookie=on_load_cookie,
    on_invalid_cookie=on_invalid_cookie,
    on_missing_session=on_missing_session,
)


@app.post("/init/")
async def init_session(
    response: Response, manager: SessionManager = Depends(get_session_manager)
) -> Response:
    response = manager.open_session(response, await session_id_generator(app))
    response.status_code = status.HTTP_200_OK
    return response


@app.post("/set/{key}/{value}/")
async def add_to_session(
    key: str,
    value: Any,
    session: AsyncSession = Depends(get_user_session),
) -> Response:
    """Add the value to the session by the key"""
    result = await session.set(key, value)
    return Response(status_code=status.HTTP_200_OK)


@app.post("/get/{key}/")
async def get_from_session(
    key: str, session: AsyncSession = Depends(get_user_session)
) -> Response:
    """Get a session value by the key"""
    if not await session.exists(key):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    value = list(await session.get(key)).pop()
    return JSONResponse(content={key: value}, status_code=status.HTTP_200_OK)


@app.post("/remove/{key}")
async def remove_from_session(
    key: str, session: AsyncSession = Depends(get_user_session)
) -> Response:
    if not await session.exists(key):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    await session.delete(key)
    return Response(status_code=status.HTTP_200_OK)


@app.post("/flush/")
async def flush_session(session: AsyncSession = Depends(get_user_session)) -> Response:
    await session.clear()
    return Response(status_code=status.HTTP_200_OK)


@app.post("/close/")
async def close_session(
    response: Response,
    manager: SessionManager = Depends(get_session_manager),
) -> Response:
    response = manager.close_session(response)
    response.status_code = status.HTTP_200_OK
    return response
