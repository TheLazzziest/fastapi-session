from fastapi import status
from fastapi.exceptions import HTTPException


class BaseSessionException(HTTPException):
    """A base exception for the package."""


class BackendImportException(BaseSessionException):
    """An exception indicatating the error occurred during backend initialization."""

    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: str = None,
    ) -> None:
        super().__init__(status_code, detail)


class MissingSessionException(BaseSessionException):
    """An exception for notifying a missing user session."""

    def __init__(
        self,
        status_code: int = status.HTTP_401_UNAUTHORIZED,
        detail: str = None,
    ) -> None:
        super().__init__(status_code, detail)


class InvalidCookieException(BaseSessionException):
    """An exception for notifying a passed invalid cookie"""

    def __init__(
        self,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        detail: str = None,
    ) -> None:
        super().__init__(status_code, detail)
