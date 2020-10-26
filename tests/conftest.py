"""Global test configuration."""
import pytest
from pathlib import PurePath
from junk_drawer import Store
from junk_drawer.filesystem import AsyncFilesystemLike, AsyncFilesystem
from .helpers import CoolModel

# TODO(mc, 2020-09-28): mypy doesn't know about mock.AsyncMock
from mock import AsyncMock, MagicMock  # type: ignore[attr-defined]


STORE_PATH_STR = "./store"


@pytest.fixture
def mock_filesystem():
    """Create a mock asynchronous filesystem."""
    return AsyncMock(spec=AsyncFilesystemLike)


@pytest.fixture
def filesystem() -> AsyncFilesystemLike:
    """Create a real asynchronous filesystem."""
    return AsyncFilesystem()


@pytest.fixture
def mock_parse_json():
    """Mock parse JSON function."""
    return MagicMock()


@pytest.fixture
def mock_encode_json():
    """Mock encode JSON function."""
    return MagicMock()


@pytest.fixture
def store_path():
    """Store fixture directory path."""
    return PurePath(STORE_PATH_STR)


@pytest.fixture
def real_store_path(tmp_path):
    """Actual Store directory path."""
    return PurePath(tmp_path) / STORE_PATH_STR


@pytest.fixture
def store(store_path, mock_filesystem) -> Store:
    """Create a fresh Store with a mock filesystem."""
    return Store(
        directory=store_path,
        schema=CoolModel,
        primary_key=None,
        migrations=(),
        ignore_errors=False,
        filesystem=mock_filesystem,
    )


@pytest.fixture
def keyed_store(store_path, mock_filesystem) -> Store:
    """Create a Store with a primary key mock filesystem."""
    return Store(
        directory=store_path,
        schema=CoolModel,
        primary_key="foo",
        migrations=(),
        ignore_errors=False,
        filesystem=mock_filesystem,
    )


@pytest.fixture
def ignore_errors_store(store_path, mock_filesystem) -> Store:
    """Create a Store with errors ignored."""
    return Store(
        directory=store_path,
        schema=CoolModel,
        primary_key=None,
        migrations=(),
        ignore_errors=True,
        filesystem=mock_filesystem,
    )
