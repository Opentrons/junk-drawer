"""Store tests for junk_drawer."""
import pytest
from pathlib import PurePath
from pydantic import BaseModel
from junk_drawer import Store
from junk_drawer.errors import InvalidItemDataError, ItemAccessError
from junk_drawer.filesystem import (
    AsyncFilesystemLike,
    DirectoryEntry as DirEntry,
    PathNotFoundError,
    FileReadError,
    FileParseError,
)

# TODO(mc, 2020-09-28): mypy doesn't know about mock.AsyncMock
from mock import AsyncMock  # type: ignore[attr-defined]


pytestmark = pytest.mark.asyncio


class CoolModel(BaseModel):
    """Simple Pydantic model for to act as the Store's schema."""

    foo: str
    bar: int


@pytest.fixture
def fs_adapter():
    """Mock an asynchronous filesystem."""
    return AsyncMock(spec=AsyncFilesystemLike)


@pytest.fixture
async def store(fs_adapter):
    """Create a fresh Store for every test."""
    store = await Store.create(
        "./store",
        schema=CoolModel,
        filesystem=fs_adapter,
    )
    return store


dir_path = PurePath("./store")


async def test_store_create(store, fs_adapter):
    """It should be able to create a Store backed by a directory."""
    assert type(store) == Store
    fs_adapter.ensure_dir.assert_called_with(PurePath("./store"))


async def test_store_exists_with_nonexistent_key(store, fs_adapter):
    """It should return False from store.exists if file doesn't exist."""
    fs_adapter.file_exists.return_value = False
    exists = await store.exists("foo")

    assert exists is False
    fs_adapter.file_exists.assert_called_with(PurePath("./store/foo"))


async def test_store_exists_with_existing_key(store, fs_adapter):
    """It should return True from store.exists if file exists."""
    fs_adapter.file_exists.return_value = True
    exists = await store.exists("foo")

    assert exists is True


async def test_store_get_with_nonexistent_key(store, fs_adapter):
    """It should return None from store.get if file doesn't exist."""
    fs_adapter.read_json.side_effect = PathNotFoundError()
    item = await store.get("foo")

    assert item is None
    fs_adapter.read_json.assert_called_with(
        PurePath("./store/foo"), parse_json=CoolModel.parse_raw
    )


async def test_store_get_returns_read_result(store, fs_adapter):
    """It should return a model from store.get if file exists."""
    result = CoolModel(foo="bar", bar=42)
    fs_adapter.read_json.return_value = result
    item = await store.get("foo")

    assert item == result
    fs_adapter.read_json.assert_called_with(
        PurePath("./store/foo"), parse_json=CoolModel.parse_raw
    )


async def test_store_reads_dir_for_get_all_keys(store, fs_adapter):
    """It should read the directory and return all JSON files as keys."""
    fs_adapter.read_dir.return_value = ["foo", "bar", "baz"]
    keys = await store.get_all_keys()

    assert keys == ["foo", "bar", "baz"]
    fs_adapter.read_dir.assert_called_with(PurePath("./store"))


async def test_store_reads_whole_dir_for_get_all_entries(store, fs_adapter):
    """It should reads for all files in the directory to get all entries."""
    fs_adapter.read_json_dir.return_value = [
        DirEntry(path=dir_path / "foo", contents=CoolModel(foo="hello", bar=0)),
        DirEntry(path=dir_path / "bar", contents=CoolModel(foo="from the", bar=1)),
        DirEntry(path=dir_path / "baz", contents=CoolModel(foo="other side", bar=2)),
    ]
    items = await store.get_all_entries()

    assert items[0] == ("foo", CoolModel(foo="hello", bar=0))
    assert items[1] == ("bar", CoolModel(foo="from the", bar=1))
    assert items[2] == ("baz", CoolModel(foo="other side", bar=2))
    fs_adapter.read_json_dir.assert_called_with(
        PurePath("./store"), parse_json=CoolModel.parse_raw, ignore_errors=False
    )


async def test_store_reads_whole_dir_for_get_all_items(store, fs_adapter):
    """It should read all files in the directory to get all items."""
    fs_adapter.read_json_dir.return_value = [
        DirEntry(path=dir_path / "foo", contents=CoolModel(foo="hello", bar=0)),
        DirEntry(path=dir_path / "bar", contents=CoolModel(foo="from the", bar=1)),
        DirEntry(path=dir_path / "baz", contents=CoolModel(foo="other side", bar=2)),
    ]
    items = await store.get_all_items()

    assert items[0] == CoolModel(foo="hello", bar=0)
    assert items[1] == CoolModel(foo="from the", bar=1)
    assert items[2] == CoolModel(foo="other side", bar=2)
    fs_adapter.read_json_dir.assert_called_with(
        PurePath("./store"), parse_json=CoolModel.parse_raw, ignore_errors=False
    )


async def test_store_get_raises_invalid_json(store, fs_adapter):
    """It should raise a validation error if the data fails to parse."""
    fs_adapter.read_json.side_effect = FileParseError("oh no")
    fs_adapter.read_json_dir.side_effect = FileParseError("oh no")

    with pytest.raises(InvalidItemDataError, match=r".*oh no.*"):
        await store.get("foo")

    with pytest.raises(InvalidItemDataError, match=r".*oh no.*"):
        await store.get_all_items()


async def test_store_get_raises_read_error(store, fs_adapter):
    """It should raise an access error if the data fails to read."""
    fs_adapter.read_json.side_effect = FileReadError("oh no")
    fs_adapter.read_json_dir.side_effect = FileReadError("oh no")

    with pytest.raises(ItemAccessError, match=r".*oh no.*"):
        await store.get("foo")

    with pytest.raises(ItemAccessError, match=r".*oh no.*"):
        await store.get_all_items()


async def test_validation_error_may_be_silenced(fs_adapter):
    """It should return None in case of a validation error if set to not raise."""
    store = await Store.create(
        "./store",
        schema=CoolModel,
        filesystem=fs_adapter,
        ignore_errors=True,
    )
    fs_adapter.read_json.side_effect = FileParseError("oh no")
    fs_adapter.read_json_dir.return_value = [
        DirEntry(path=dir_path / "foo", contents=CoolModel(foo="hello", bar=0)),
    ]
    item = await store.get("foo")
    all_items = await store.get_all_items()

    assert item is None
    assert all_items == [CoolModel(foo="hello", bar=0)]
    fs_adapter.read_json_dir.assert_called_with(
        PurePath("./store"), parse_json=CoolModel.parse_raw, ignore_errors=True
    )
