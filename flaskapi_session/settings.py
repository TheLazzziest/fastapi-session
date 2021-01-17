"""A module which contains settings for managing different parts of session storage."""

# Types of backend
MEMORY_BACKEND_TYPE: str = "flaskapi_session.backends.MemoryBackend"
FS_BACKEND_TYPE: str = "flaskapi_session.backends.FSBackend"
REDIS_BACKEND_TYPE: str = "flaskapi_session.backends.RedisBackend"
DATABASE_BACKEND_TYPE: str = "flaskapi_session.backends.DBBackend"


# Cookie settings
FAPI_SESSION_ID_KEY: str = "FAPISESSID"