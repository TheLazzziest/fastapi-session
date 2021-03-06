import pytest
import typing
from datetime import datetime, timedelta

import pendulum
from cryptography.fernet import Fernet, InvalidToken, InvalidSignature

from fastapi_session import (
    AES_SIV_Encryptor,
    create_namespace,
    decrypt_session,
    encrypt_session,
    SessionSettings,
)


def test_create_namespace(encryptor: AES_SIV_Encryptor, subtests: typing.Any):
    """Check that a namespace is always deterministic."""
    data = (
        (
            "firstuser",
            "MjA4ZTU2ZTMzM2EzMzQ1YWI2OjNhNTA0NjA3ZTkwZTgyNjI3YWFiYTY0YWViYmNiZTMz",
        ),
        (
            "seconduser",
            "ZTFjYTA0YTU4MDcwZmQxYzVlNTU6ODUyZmE3YWNiNWE5ZTU4MDNkYjY3NDhkNjJlNjU5Mjk=",
        ),
    )
    for session_id, ns in data:
        with subtests.test(msg=f"A session with id: {session_id}"):
            create_namespace(encryptor, session_id) == ns


@pytest.mark.parametrize(
    "current_time",
    [
        pendulum.from_format("2021-02-05 12:31:01", "YYYY-MM-DD HH:mm:SS"),
        pendulum.from_format("2021-02-05 12:31:01", "YYYY-MM-DD HH:mm:SS").timestamp(),
    ],
)
def test_session_encryption(
    signer: typing.Type[Fernet],
    session_id: str,
    current_time: typing.Union[int, datetime],
):
    signed_token = encrypt_session(signer, session_id, current_time)
    assert decrypt_session(signer, signed_token) == session_id


@pytest.mark.parametrize("ttl", [None, pendulum.now().add(seconds=60)])
def test_session_decryption(
    signer: typing.Type[Fernet],
    token: str,
    session_id: str,
    ttl: typing.Union[type(None), int, datetime],
):
    assert decrypt_session(signer, token, ttl) == session_id


@pytest.mark.parametrize(
    "invalid_token",
    [
        # modified tokens
        "gAAAAABgHTqEqIxk02R1e5GpCuOz1sRQTmxWCvVf1Js3TJKjla62_NQ2OMxf0ciqbNmtWbVywvb5onvhccuOY-uX-NB7-n2uN1Fmnunyu8ErGi4KRkywdpIVMQ5qhLYDOatHqjOSzbfC",
    ],
)
def test_invalid_token(signer: typing.Type[Fernet], invalid_token: str):
    # Test cases when a cookie represents an invalid signature or it's just tempered
    with pytest.raises(InvalidToken):
        decrypt_session(signer, invalid_token)


@pytest.mark.parametrize(
    "ttl", [timedelta(seconds=1).total_seconds(), pendulum.yesterday()]
)
def test_token_invalidation_by_ttl(
    signer: typing.Type[Fernet], token: bytes, ttl: typing.Union[int, datetime]
):
    with pytest.raises(InvalidToken):
        decrypt_session(signer, token, ttl)
