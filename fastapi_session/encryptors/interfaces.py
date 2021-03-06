import typing

from abc import ABC, abstractmethod

__all__ = ("AES_SIV_Encryptor",)


class EncryptorInterface(ABC):
    """An interface for providing encryption/decryption methods for session data."""

    @abstractmethod
    def __init__(
        self,
        secret: str,
        iv: typing.Optional[bytes] = None,
        nonce: typing.Optional[bytes] = None,
    ):
        raise NotImplementedError

    @abstractmethod
    def encrypt(self, *, message: str, **kwargs: typing.Optional[typing.Any]) -> str:
        """Encrypt the passed message using the current cipher."""
        raise NotImplementedError

    @abstractmethod
    def decrypt(self, message: str, **kwargs: typing.Optional[typing.Any]) -> str:
        """Decrypt the encrypted message using the current cipher."""
        raise NotImplementedError