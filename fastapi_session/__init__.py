from pathlib import Path

from .backends import (
    BackendInterface,
    DBBackend,
    FSBackend,
    RedisBackend,
)
from .constants import FS_BACKEND_TYPE, DATABASE_BACKEND_TYPE, REDIS_BACKEND_TYPE
from .dependencies import get_session_manager, get_user_session
from .encryptors import EncryptorInterface, AES_SIV_Encryptor
from .exceptions import (
    BackendImportException,
    MissingSessionException,
    InvalidCookieException,
)
from .managers import SessionManager, create_session_manager
from .middlewares import SessionMiddleware
from .sessions import AsyncSession
from .settings import get_session_settings, SessionSettings
from .types import Connection
from .utils import (
    create_backend,
    create_namespace,
    decrypt_session,
    encrypt_session,
    import_backend,
)

__all__ = (
    AES_SIV_Encryptor,
    AsyncSession,
    BackendInterface,
    BackendImportException,
    Connection,
    create_backend,
    create_namespace,
    create_session_manager,
    DATABASE_BACKEND_TYPE,
    DBBackend,
    decrypt_session,
    encrypt_session,
    EncryptorInterface,
    FSBackend,
    FS_BACKEND_TYPE,
    get_session_manager,
    get_session_settings,
    get_user_session,
    InvalidCookieException,
    import_backend,
    MissingSessionException,
    RedisBackend,
    REDIS_BACKEND_TYPE,
    SessionManager,
    SessionManager,
    SessionMiddleware,
)

__version__ = "0.8.3"
