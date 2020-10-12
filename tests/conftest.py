"""Global test configuration."""
import pytest
from junk_drawer import Store
from junk_drawer.filesystem import AsyncFilesystemLike, AsyncFilesystem
from .helpers import CoolModel, STORE_PATH_STR

# TODO(mc, 2020-09-28): mypy doesn't know about mock.AsyncMock
from mock import AsyncMock, MagicMock  # type: ignore[attr-defined]


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
async def store(mock_filesystem) -> Store:
    """Create a fresh Store with a mock filesyste."""
    store = await Store.create(
        STORE_PATH_STR,
        schema=CoolModel,
        filesystem=mock_filesystem,
    )
    return store


@pytest.fixture
async def keyed_store(mock_filesystem) -> Store:
    """Create a Store with a primary key mock filesystem."""
    store = await Store.create(
        STORE_PATH_STR,
        schema=CoolModel,
        primary_key="foo",
        filesystem=mock_filesystem,
    )
    return store
