import logging
import typing
import json
from base64 import b64encode
from hashlib import sha256
from typing import Any, List

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from fastapi import Depends, FastAPI, Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi_session import (
    Connection,
    AsyncSession,
    get_session_manager,
    get_user_session,
    MissingSessionException,
    SessionManager,
    SessionSettings,
)
from fastapi_session.adapters.fastapi import connect

logger = logging.getLogger(__name__)

app = FastAPI()
settings = SessionSettings()
secret_key = "2BCuqD_9qwuq4zXMdVPWfWwrLgdrET_OymqiS_Ubo_o"
salt = sha256(secret_key.encode("utf-8")).hexdigest().encode("utf-8")


async def session_id_generator(app: FastAPI) -> str:
    """A delegate for generating of a session id."""
    return sha256("4bf9c729-ca23-4898-b314-db8f5c41607c".encode("utf-8")).hexdigest()


@app.exception_handler(MissingSessionException)
async def on_missing_session(request: Request) -> None:
    """A delegate for restoring of a session id from the passed cookie."""
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


async def on_load_cookie(request: Request, cookie: str) -> str:
    return cookie


@app.exception_handler(Exception)
async def on_invalid_cookie(request: Request, exc: InvalidToken) -> Response:
    response = Response(status_code=status.HTTP_401_UNAUTHORIZED)
    response.unset_cookie(settings.COOKIE_NAME)
    return response


connect(
    app=app,
    secret=secret_key,
    signer=Fernet(
        b64encode(
            PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100,
            ).derive(secret_key.encode("utf-8"))
        )
    ),
    on_load_cookie=on_load_cookie,
)


@app.on_event("shutdown")
async def close_session():
    await app.session.save()


@app.post("/init/")
async def init_session(
    response: Response, manager: SessionManager = Depends(get_session_manager)
) -> Response:
    response = manager.set_cookie(response, await session_id_generator(app))
    response.status_code = status.HTTP_200_OK
    return response


@app.post("/set/{key}/{value}/")
async def add_to_session(
    key: str,
    value: Any,
    session: AsyncSession = Depends(get_user_session),
) -> Response:
    """Add the value to the session by the key"""
    await session.set(key, value)
    await session.save()
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
    await session.save()
    return Response(status_code=status.HTTP_200_OK)


@app.post("/flush/")
async def flush_session(session: AsyncSession = Depends(get_user_session)) -> Response:
    await session.clear()
    await session.save()
    return Response(status_code=status.HTTP_200_OK)


@app.post("/close/")
async def close_session(
    response: Response, manager: SessionManager = Depends(get_session_manager)
) -> Response:
    response = manager.unset_cookie(response)
    response.status_code = status.HTTP_200_OK
    return response
