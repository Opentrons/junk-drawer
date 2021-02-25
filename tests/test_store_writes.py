"""Store tests for junk_drawer."""
import pytest
from mock import AsyncMock  # type: ignore[attr-defined]
from pathlib import PurePosixPath

from junk_drawer import Store
from junk_drawer.errors import ItemAccessError, ItemEncodeError
from junk_drawer.filesystem import (
    PathNotFoundError,
    RemoveFileError,
    FileWriteError,
    FileEncodeError,
)
from .helpers import CoolModel


pytestmark = pytest.mark.asyncio


async def test_delete_store(
    store: Store[CoolModel], store_path: PurePosixPath, mock_filesystem: AsyncMock
) -> None:
    """store.delete_store should remove the directory."""
    await store.delete_store()
    mock_filesystem.remove_dir.assert_called_with(store_path)


def test_delete_store_sync(
    store: Store[CoolModel], store_path: PurePosixPath, mock_filesystem: AsyncMock
) -> None:
    """store.delete_store should remove the directory."""
    store.delete_store_sync()
    mock_filesystem.sync.remove_dir.assert_called_with(store_path)


async def test_delete_item(
    store: Store[CoolModel], store_path: PurePosixPath, mock_filesystem: AsyncMock
) -> None:
    """store.delete should remove a file."""
    key = "delete-me"
    removed = await store.delete(key)

    assert removed == key
    mock_filesystem.remove.assert_called_with(store_path / key)


async def test_delete_sync(
    store: Store[CoolModel], store_path: PurePosixPath, mock_filesystem: AsyncMock
) -> None:
    """store.delete_sync should remove a file."""
    key = "delete-me"
    removed = store.delete_sync(key)

    assert removed == key
    mock_filesystem.sync.remove.assert_called_with(store_path / key)


async def test_delete_nonexistent_key(
    store: Store[CoolModel], mock_filesystem: AsyncMock
) -> None:
    """store.delete should return None if path does not exist."""
    key = "delete-me"
    mock_filesystem.remove.side_effect = PathNotFoundError("oh no")
    removed = await store.delete(key)

    assert removed is None


def test_delete_sync_nonexistent_key(
    store: Store[CoolModel], mock_filesystem: AsyncMock
) -> None:
    """store.delete_sync should return None if path does not exist."""
    key = "delete-me"
    mock_filesystem.sync.remove.side_effect = PathNotFoundError("oh no")
    removed = store.delete_sync(key)

    assert removed is None


async def test_delete_with_access_error(
    store: Store[CoolModel], mock_filesystem: AsyncMock
) -> None:
    """store.delete should raise an ItemAccessError if file can't be removed."""
    key = "delete-me"
    mock_filesystem.remove.side_effect = RemoveFileError("oh no")

    with pytest.raises(ItemAccessError, match="oh no"):
        await store.delete(key)


def test_delete_sync_with_access_error(
    store: Store[CoolModel], mock_filesystem: AsyncMock
) -> None:
    """store.delete_sync should raise an ItemAccessError if file can't be removed."""
    key = "delete-me"
    mock_filesystem.sync.remove.side_effect = RemoveFileError("oh no")

    with pytest.raises(ItemAccessError, match="oh no"):
        store.delete_sync(key)


async def test_store_put(
    store: Store[CoolModel], store_path: PurePosixPath, mock_filesystem: AsyncMock
) -> None:
    """store.put should call filesystem.write_json."""
    key = "cool-key"
    item = CoolModel(foo="hello", bar=0)
    added_key = await store.put(item, key)

    assert added_key == key
    mock_filesystem.write_json.assert_called_with(
        store_path / key,
        item,
        encode_json=store.encode_json,
    )


def test_store_put_sync(
    store: Store[CoolModel], store_path: PurePosixPath, mock_filesystem: AsyncMock
) -> None:
    """store.put should call filesystem.write_json."""
    key = "cool-key"
    item = CoolModel(foo="hello", bar=0)
    added_key = store.put_sync(item, key)

    assert added_key == key
    mock_filesystem.sync.write_json.assert_called_with(
        store_path / key,
        item,
        encode_json=store.encode_json,
    )


async def test_store_put_raises_access_error(
    store: Store[CoolModel], mock_filesystem: AsyncMock
) -> None:
    """store.put should raise an ItemAccessError if file cannot be written."""
    key = "cool-key"
    mock_filesystem.write_json.side_effect = FileWriteError("oh no")

    with pytest.raises(ItemAccessError, match="oh no"):
        await store.put(CoolModel(foo="hello", bar=0), key)


def test_store_put_sync_raises_access_error(
    store: Store[CoolModel], mock_filesystem: AsyncMock
) -> None:
    """store.put_sync should raise an ItemAccessError if file cannot be written."""
    key = "cool-key"
    mock_filesystem.sync.write_json.side_effect = FileWriteError("oh no")

    with pytest.raises(ItemAccessError, match="oh no"):
        store.put_sync(CoolModel(foo="hello", bar=0), key)


async def test_store_put_raises_encode_error(
    store: Store[CoolModel], mock_filesystem: AsyncMock
) -> None:
    """store.put should raise an ItemAccessError if file cannot be written."""
    key = "cool-key"
    mock_filesystem.write_json.side_effect = FileEncodeError("oh no")

    with pytest.raises(ItemEncodeError, match="oh no"):
        await store.put(CoolModel(foo="hello", bar=0), key)


def test_store_put_sync_raises_encode_error(
    store: Store[CoolModel], mock_filesystem: AsyncMock
) -> None:
    """store.put_sync should raise an ItemAccessError if file cannot be written."""
    key = "cool-key"
    mock_filesystem.sync.write_json.side_effect = FileEncodeError("oh no")

    with pytest.raises(ItemEncodeError, match="oh no"):
        store.put_sync(CoolModel(foo="hello", bar=0), key)


async def test_store_put_with_primary_key(
    keyed_store: Store[CoolModel], store_path: PurePosixPath, mock_filesystem: AsyncMock
) -> None:
    """store.put should pull primary key from the model if available."""
    item = CoolModel(foo="hello", bar=0)
    put_key = await keyed_store.put(item)

    assert put_key == "hello"
    mock_filesystem.write_json.assert_called_with(
        store_path / "hello",
        item,
        encode_json=keyed_store.encode_json,
    )


def test_store_put_sync_with_primary_key(
    keyed_store: Store[CoolModel], store_path: PurePosixPath, mock_filesystem: AsyncMock
) -> None:
    """store.put_sync should pull primary key from the model if available."""
    item = CoolModel(foo="hello", bar=0)
    put_key = keyed_store.put_sync(item)

    assert put_key == "hello"
    mock_filesystem.sync.write_json.assert_called_with(
        store_path / "hello",
        item,
        encode_json=keyed_store.encode_json,
    )


async def test_store_put_with_non_string_primary_key(
    keyed_store: Store[CoolModel], mock_filesystem: AsyncMock
) -> None:
    """store.put should cast primary key from the model to string."""
    item = CoolModel(foo=101, bar=0)
    put_key = await keyed_store.put(item)

    assert type(put_key) == str
    assert put_key == "101"


def test_store_put_sync_with_non_string_primary_key(
    keyed_store: Store[CoolModel], mock_filesystem: AsyncMock
) -> None:
    """store.put should cast primary key from the model to string."""
    item = CoolModel(foo=101, bar=0)
    put_key = keyed_store.put_sync(item)

    assert type(put_key) == str
    assert put_key == "101"


async def test_store_put_missing_key_asserts(
    store: Store[CoolModel], mock_filesystem: AsyncMock
) -> None:
    """store.put should assert if used without an explicit key."""
    item = CoolModel(foo="hello", bar=0)

    with pytest.raises(AssertionError, match="key.+required"):
        await store.put(item)


def test_store_put_sync_missing_key_asserts(
    store: Store[CoolModel], mock_filesystem: AsyncMock
) -> None:
    """store.put_sync should assert if used without an explicit key."""
    item = CoolModel(foo="hello", bar=0)

    with pytest.raises(AssertionError, match="key.+required"):
        store.put_sync(item)


async def test_store_put_bad_primary_key_asserts(
    store_path: PurePosixPath, mock_filesystem: AsyncMock
) -> None:
    """store.put should assert if primary_key isn't in the model."""
    store = Store(
        directory=store_path,
        schema=CoolModel,
        primary_key="not-a-field",
        migrations=(),
        ignore_errors=False,
        filesystem=mock_filesystem,
    )
    item = CoolModel(foo="hello", bar=0)

    with pytest.raises(AssertionError, match="key.+required"):
        await store.put(item)


def test_store_put_sync_bad_primary_key_asserts(
    store_path: PurePosixPath, mock_filesystem: AsyncMock
) -> None:
    """store.put_sync should assert if primary_key isn't in the model."""
    store = Store(
        directory=store_path,
        schema=CoolModel,
        primary_key="not-a-field",
        migrations=(),
        ignore_errors=False,
        filesystem=mock_filesystem,
    )
    item = CoolModel(foo="hello", bar=0)

    with pytest.raises(AssertionError, match="key.+required"):
        store.put_sync(item)


async def test_store_put_returns_none_if_ignoring_errors(
    ignore_errors_store: Store[CoolModel], mock_filesystem: AsyncMock
) -> None:
    """store.put should return None if item cannot be encoded / written."""
    key = "cool-key"
    mock_filesystem.write_json.side_effect = FileWriteError("oh no")
    result = await ignore_errors_store.put(CoolModel(foo="hello", bar=0), key)

    assert result is None

    mock_filesystem.write_json.side_effect = FileEncodeError("oh no")
    result = await ignore_errors_store.put(CoolModel(foo="hello", bar=0), key)

    assert result is None


def test_store_put_sync_returns_none_if_ignoring_errors(
    ignore_errors_store: Store[CoolModel], mock_filesystem: AsyncMock
) -> None:
    """store.put should return None if item cannot be encoded / written."""
    key = "cool-key"
    mock_filesystem.sync.write_json.side_effect = FileWriteError("oh no")
    result = ignore_errors_store.put_sync(CoolModel(foo="hello", bar=0), key)

    assert result is None

    mock_filesystem.sync.write_json.side_effect = FileEncodeError("oh no")
    result = ignore_errors_store.put_sync(CoolModel(foo="hello", bar=0), key)

    assert result is None


async def test_store_ensure(
    store: Store[CoolModel], mock_filesystem: AsyncMock
) -> None:
    """store.ensure should return item if it exists already."""
    default_item = CoolModel(foo="foo", bar=0)
    existing_item = CoolModel(foo="bar", bar=1)
    mock_filesystem.read_json.return_value = existing_item

    item = await store.ensure(default_item, "foo")

    assert item == existing_item


def test_store_ensure_sync(store: Store[CoolModel], mock_filesystem: AsyncMock) -> None:
    """store.ensure_sync should return item if it exists already."""
    default_item = CoolModel(foo="foo", bar=0)
    existing_item = CoolModel(foo="bar", bar=1)
    mock_filesystem.sync.read_json.return_value = existing_item

    item = store.ensure_sync(default_item, "foo")

    assert item == existing_item


async def test_store_ensure_writes_default(
    store: Store[CoolModel], store_path: PurePosixPath, mock_filesystem: AsyncMock
) -> None:
    """store.ensure should write default item and return it."""
    default_item = CoolModel(foo="foo", bar=0)
    mock_filesystem.read_json.side_effect = PathNotFoundError()

    item = await store.ensure(default_item, "foo")

    assert item == default_item
    mock_filesystem.write_json.assert_called_with(
        store_path / "foo",
        default_item,
        encode_json=store.encode_json,
    )


def test_store_ensure_sync_writes_default(
    store: Store[CoolModel], store_path: PurePosixPath, mock_filesystem: AsyncMock
) -> None:
    """store.ensure_sync should write default item and return it."""
    default_item = CoolModel(foo="foo", bar=0)
    mock_filesystem.sync.read_json.side_effect = PathNotFoundError()

    item = store.ensure_sync(default_item, "foo")

    assert item == default_item
    mock_filesystem.sync.write_json.assert_called_with(
        store_path / "foo",
        default_item,
        encode_json=store.encode_json,
    )


async def test_store_ensure_with_primary_key(
    keyed_store: Store[CoolModel], mock_filesystem: AsyncMock
) -> None:
    """store.ensure should return item if it exists already."""
    default_item = CoolModel(foo="foo", bar=0)
    existing_item = CoolModel(foo="bar", bar=1)
    mock_filesystem.read_json.return_value = existing_item

    item = await keyed_store.ensure(default_item)

    assert item == existing_item


def test_store_ensure_sync_with_primary_key(
    keyed_store: Store[CoolModel], mock_filesystem: AsyncMock
) -> None:
    """store.ensure should return item if it exists already."""
    default_item = CoolModel(foo="foo", bar=0)
    existing_item = CoolModel(foo="bar", bar=1)
    mock_filesystem.sync.read_json.return_value = existing_item

    item = keyed_store.ensure_sync(default_item)

    assert item == existing_item
