import logging
import typing
import json
import secrets
from http import HTTPStatus
from hashlib import sha256
from typing import Any, List
from uuid import uuid4

from itsdangerous.exc import BadTimeSignature, SignatureExpired
from fastapi import Depends, FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse
from fastapi_session import (
    FS_BACKEND_TYPE,
    SessionManager,
    SessionSettings,
    CookieManager,
    CookieSessionMiddleware,
)


async def session_id_generator(app: FastAPI) -> str:
    """A delegate for generating of a session id."""
    secret_key = app.state.secret_key
    return sha256(f"{secret_key}:{uuid4()}".encode("utf-8")).hexdigest()


async def session_id_loader(cookie: object) -> Any:
    """A delegate for restoring of a session id from the passed cookie."""
    return cookie


def invalid_cookie_callback(
    request: Request, exc: typing.Union[BadTimeSignature, SignatureExpired]
) -> Response:
    settings = request.app.state.settings
    response = Response(status_code=HTTPStatus.BAD_REQUEST)
    response.delete_cookie(settings.SESSION_ID_KEY)
    return response


logger = logging.getLogger(__name__)

app = FastAPI()
secret_key = secrets.token_urlsafe(32)
settings = SessionSettings()
cookie = CookieManager(
    secret_key=secret_key,
    session_cookie=settings.SESSION_ID_KEY,
)
session = SessionManager(
    secret_key=secret_key,
    backend_type=FS_BACKEND_TYPE,
    session_id_loader=session_id_loader,
)
app.state.secret_key = secret_key
app.state.settings = settings

# Connect a session middleware to the FastAPI app
app.add_middleware(
    CookieSessionMiddleware,
    cookie_manager=cookie,
    session_manager=session,
    on_invalid_cookie=invalid_cookie_callback,
)


@app.post("/init/")
async def init_session(response: Response) -> Response:
    response = cookie.set_cookie(response, await session_id_generator(app))
    response.status_code = HTTPStatus.OK
    return response


@app.post("/set/{key}/{value}/")
async def add_to_session(
    request: Request, response: Response, key: str, value: Any
) -> Response:
    """Add the value to the session by the key"""
    if "session" not in request:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST)
    await request.session.set(key, value)
    await request.session.save()
    response.status_code = HTTPStatus.OK
    return response


@app.post("/get/{key}/")
async def get_from_session(request: Request, response: Response, key: str) -> Response:
    """Get a session value by the key"""
    if "session" not in request:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST)
    value = list(await request.session.get(key)).pop()
    return JSONResponse(content={key: value}, status_code=HTTPStatus.OK)


@app.post("/flush/")
async def flush_session(request: Request, response: Response) -> Response:
    if "session" not in request:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST)
    await request.session.clear()
    await request.session.save()
    response.status_code = HTTPStatus.OK
    return response


@app.post("/close/")
async def close_session(request: Request, response: Response) -> Response:
    response = cookie.remove_cookie(response)
    response.status_code = HTTPStatus.OK
    return response
