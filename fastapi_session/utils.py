import typing
import json
from datetime import datetime

import pendulum
from base64 import b64decode, b64encode
from importlib import import_module

from cryptography.fernet import Fernet, InvalidToken

from .backends import BackendInterface
from .encryptors import EncryptorInterface
from .exceptions import BackendImportException


def import_backend(backend_path: str) -> typing.Optional[BackendInterface]:
    """Import a session backend class."""
    path, backend_type = backend_path.rsplit(".", 1)
    try:
        module = import_module(path)
        klass = getattr(module, backend_type, None)
        if klass is None:
            raise AttributeError(f"Undefined property {backend_type} in {path}")
        return klass
    except (ImportError, AttributeError) as e:
        # AttributeError doesn't have msg property
        raise BackendImportException(detail=e.args[0]) from e


async def create_backend(
    backend_path: str, *args, **kwargs
) -> typing.Type[BackendInterface]:
    klass: typing.Optional[BackendInterface] = import_backend(backend_path)
    if not issubclass(klass, BackendInterface):
        raise TypeError(f"The unsupported backend type: {klass.__class__}")
    return await klass.create(*args, **kwargs)


def create_namespace(
    encryptor: typing.Type[EncryptorInterface], session_id: str
) -> str:
    """Generate a session namespace based on a fernet instance and a user session id."""
    return encryptor.encrypt(session_id)


def encrypt_session(
    signer: typing.Type[Fernet],
    session_id: str,
    current_time: typing.Optional[typing.Union[int, datetime]] = None,
) -> str:

    """An utility for generating a token from the passed session id.

    :param signer: an instance of a fernet object
    :param session_id: a user session id
    :param current_time: a datetime object or timestamp indicating the time of the session id encryption. By default, it is now
    """
    if current_time is None:
        current_time = pendulum.now()
    if isinstance(current_time, datetime):
        current_time = current_time.timestamp()
    return signer.encrypt_at_time(session_id.encode("utf-8"), int(current_time)).decode(
        "utf-8"
    )


def decrypt_session(
    signer: typing.Type[Fernet],
    token: str,
    ttl: typing.Optional[typing.Union[int, datetime]] = None,
) -> str:
    """An utility for extracting a user payload from the passed token.

    :param cookie: a user cookie
    :param secret: an app secret key
    :param signings: a list of allowed singing algorithms for the cookie
    """
    if ttl is not None and isinstance(ttl, datetime):
        # if ttl is set as datetime (EXPIRES is set), then we must validate it by hand
        token_timestamp = signer.extract_timestamp(token.encode("utf-8"))
        if token_timestamp >= int(ttl.timestamp()):
            raise InvalidToken(f"Token {token} is expired.")
        ttl = None
    return signer.decrypt(token.encode("utf-8"), ttl).decode("utf-8")
