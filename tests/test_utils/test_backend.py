import hashlib
import pytest
import typing

from fastapi_session import (
    import_backend,
    FS_BACKEND_TYPE,
    FSBackend,
    BackendImportError,
)


def test_import_backend():
    klass = import_backend(FS_BACKEND_TYPE)
    assert klass == FSBackend


@pytest.mark.parametrize(
    "backend_path",
    ["fastsession.backends.FS_BACKEND", "fastapi_session.backends.NonExistentBackend"],
)
def test_import_backend_error(backend_path: str):
    with pytest.raises(BackendImportError):
        import_backend(backend_path)
