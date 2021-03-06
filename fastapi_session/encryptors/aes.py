import json
import typing
from binascii import hexlify, unhexlify
from base64 import b64encode, b64decode

from Cryptodome.Cipher import AES
from Cryptodome.Protocol.KDF import PBKDF2

from .interfaces import EncryptorInterface


__all__ = ("AES_SIV_Encryptor",)


class AES_SIV_Encryptor(EncryptorInterface):
    """An encryptor using AES algorithm with SIV mode providing deterministically encrypted messages."""

    def __init__(
        self, secret: str, salt: bytes, header: typing.Optional[bytes] = "fastsession"
    ):
        self._components = ["ciphertext", "tag"]
        self._key = PBKDF2(secret, salt, 32)
        self._factory = AES
        self._mode = AES.MODE_SIV
        self._header = header

    def encrypt(self, message: str) -> bytes:
        cipher = self._factory.new(self._key, self._mode, None)
        cipher.update(self._header.encode("utf-8"))
        ciphertext, tag = cipher.encrypt_and_digest(message.encode("utf-8"))
        payload = [hexlify(x).decode("utf-8") for x in (ciphertext, tag)]
        return b64encode(":".join(payload).encode("utf-8")).decode("utf-8")

    def decrypt(self, message: str) -> str:
        cipher = self._factory.new(self._key, self._mode, None)
        cipher.update(self._header.encode("utf-8"))
        data = b64decode(message.encode("utf-8")).decode("utf-8").split(":")
        ciphertext, tag = [unhexlify(x) for x in data]
        return cipher.decrypt_and_verify(ciphertext, tag)
