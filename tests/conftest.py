"""Global test configuration."""
import pytest
from pathlib import Path, PurePosixPath
from junk_drawer import Store
from junk_drawer.filesystem import SyncFilesystem, AsyncFilesystem
from .helpers import CoolModel

# TODO(mc, 2020-09-28): mypy doesn't know about mock.AsyncMock
from mock import AsyncMock, MagicMock  # type: ignore[attr-defined]


STORE_PATH_STR = "./store"


@pytest.fixture
def mock_filesystem() -> AsyncMock:
    """Create a mock asynchronous filesystem."""
    return AsyncMock(spec=AsyncFilesystem)


@pytest.fixture
def sync_filesystem() -> SyncFilesystem:
    """Create a real synchronous filesystem."""
    return SyncFilesystem()


@pytest.fixture
def filesystem(sync_filesystem: SyncFilesystem) -> AsyncFilesystem:
    """Create a real asynchronous filesystem."""
    return AsyncFilesystem(sync_filesystem=sync_filesystem)


@pytest.fixture
def mock_parse_json() -> MagicMock:
    """Mock parse JSON function."""
    return MagicMock()


@pytest.fixture
def mock_encode_json() -> MagicMock:
    """Mock encode JSON function."""
    return MagicMock()


@pytest.fixture
def store_path() -> PurePosixPath:
    """Store fixture directory path."""
    return PurePosixPath(STORE_PATH_STR)


@pytest.fixture
def real_store_path(tmp_path: Path) -> PurePosixPath:
    """Actual Store directory path."""
    return PurePosixPath(tmp_path) / STORE_PATH_STR


@pytest.fixture
def store(store_path: PurePosixPath, mock_filesystem: AsyncMock) -> Store[CoolModel]:
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
def keyed_store(
    store_path: PurePosixPath, mock_filesystem: AsyncMock
) -> Store[CoolModel]:
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
def ignore_errors_store(
    store_path: PurePosixPath, mock_filesystem: AsyncMock
) -> Store[CoolModel]:
    """Create a Store with errors ignored."""
    return Store(
        directory=store_path,
        schema=CoolModel,
        primary_key=None,
        migrations=(),
        ignore_errors=True,
        filesystem=mock_filesystem,
    )
