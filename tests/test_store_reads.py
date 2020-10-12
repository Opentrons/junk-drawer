"""Store tests for junk_drawer."""
import pytest
from junk_drawer import Store
from junk_drawer.errors import ItemDecodeError, ItemAccessError
from junk_drawer.filesystem import (
    DirectoryEntry as DirEntry,
    PathNotFoundError,
    FileReadError,
    FileParseError,
)
from .helpers import CoolModel, store_path


pytestmark = pytest.mark.asyncio


async def test_store_create(store, mock_filesystem):
    """It should be able to create a Store backed by a directory."""
    assert type(store) == Store
    mock_filesystem.ensure_dir.assert_called_with(store_path)


async def test_store_exists_with_nonexistent_key(store, mock_filesystem):
    """It should return False from store.exists if file doesn't exist."""
    mock_filesystem.file_exists.return_value = False
    exists = await store.exists("foo")

    assert exists is False
    mock_filesystem.file_exists.assert_called_with(store_path / "foo")


async def test_store_exists_with_existing_key(store, mock_filesystem):
    """It should return True from store.exists if file exists."""
    mock_filesystem.file_exists.return_value = True
    exists = await store.exists("foo")

    assert exists is True


async def test_store_get_with_nonexistent_key(store, mock_filesystem):
    """It should return None from store.get if file doesn't exist."""
    mock_filesystem.read_json.side_effect = PathNotFoundError()
    item = await store.get("foo")

    assert item is None
    mock_filesystem.read_json.assert_called_with(
        store_path / "foo", parse_json=CoolModel.parse_raw
    )


async def test_store_get_returns_read_result(store, mock_filesystem):
    """It should return a model from store.get if file exists."""
    result = CoolModel(foo="bar", bar=42)
    mock_filesystem.read_json.return_value = result
    item = await store.get("foo")

    assert item == result
    mock_filesystem.read_json.assert_called_with(
        store_path / "foo", parse_json=CoolModel.parse_raw
    )


async def test_store_reads_dir_for_get_all_keys(store, mock_filesystem):
    """It should read the directory and return all JSON files as keys."""
    mock_filesystem.read_dir.return_value = ["foo", "bar", "baz"]
    keys = await store.get_all_keys()

    assert keys == ["foo", "bar", "baz"]
    mock_filesystem.read_dir.assert_called_with(store_path)


async def test_store_reads_whole_dir_for_get_all_entries(store, mock_filesystem):
    """It should reads for all files in the directory to get all entries."""
    mock_filesystem.read_json_dir.return_value = [
        DirEntry(path=store_path / "foo", contents=CoolModel(foo="hello", bar=0)),
        DirEntry(path=store_path / "bar", contents=CoolModel(foo="from the", bar=1)),
        DirEntry(path=store_path / "baz", contents=CoolModel(foo="other side", bar=2)),
    ]
    items = await store.get_all_entries()

    assert items[0] == ("foo", CoolModel(foo="hello", bar=0))
    assert items[1] == ("bar", CoolModel(foo="from the", bar=1))
    assert items[2] == ("baz", CoolModel(foo="other side", bar=2))
    mock_filesystem.read_json_dir.assert_called_with(
        store_path, parse_json=CoolModel.parse_raw, ignore_errors=False
    )


async def test_store_reads_whole_dir_for_get_all_items(store, mock_filesystem):
    """It should read all files in the directory to get all items."""
    mock_filesystem.read_json_dir.return_value = [
        DirEntry(path=store_path / "foo", contents=CoolModel(foo="hello", bar=0)),
        DirEntry(path=store_path / "bar", contents=CoolModel(foo="from the", bar=1)),
        DirEntry(path=store_path / "baz", contents=CoolModel(foo="other side", bar=2)),
    ]
    items = await store.get_all_items()

    assert items[0] == CoolModel(foo="hello", bar=0)
    assert items[1] == CoolModel(foo="from the", bar=1)
    assert items[2] == CoolModel(foo="other side", bar=2)
    mock_filesystem.read_json_dir.assert_called_with(
        store_path, parse_json=CoolModel.parse_raw, ignore_errors=False
    )


async def test_store_get_raises_invalid_json(store, mock_filesystem):
    """It should raise a validation error if the data fails to parse."""
    mock_filesystem.read_json.side_effect = FileParseError("oh no")
    mock_filesystem.read_json_dir.side_effect = FileParseError("oh no")

    with pytest.raises(ItemDecodeError, match=r".*oh no.*"):
        await store.get("foo")

    with pytest.raises(ItemDecodeError, match=r".*oh no.*"):
        await store.get_all_items()


async def test_store_get_raises_read_error(store, mock_filesystem):
    """It should raise an access error if the data fails to read."""
    mock_filesystem.read_json.side_effect = FileReadError("oh no")
    mock_filesystem.read_json_dir.side_effect = FileReadError("oh no")

    with pytest.raises(ItemAccessError, match=r".*oh no.*"):
        await store.get("foo")

    with pytest.raises(ItemAccessError, match=r".*oh no.*"):
        await store.get_all_items()


async def test_validation_error_may_be_silenced(mock_filesystem):
    """It should return None in case of a validation error if set to not raise."""
    store = await Store.create(
        "./store",
        schema=CoolModel,
        filesystem=mock_filesystem,
        ignore_errors=True,
    )
    mock_filesystem.read_json.side_effect = FileParseError("oh no")
    mock_filesystem.read_json_dir.return_value = [
        DirEntry(path=store_path / "foo", contents=CoolModel(foo="hello", bar=0)),
    ]
    item = await store.get("foo")
    all_items = await store.get_all_items()

    assert item is None
    assert all_items == [CoolModel(foo="hello", bar=0)]
    mock_filesystem.read_json_dir.assert_called_with(
        store_path, parse_json=CoolModel.parse_raw, ignore_errors=True
    )
