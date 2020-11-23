"""Integration tests for AsyncFilesystem read operations."""
import pytest
from mock import MagicMock
from pathlib import Path
from junk_drawer.filesystem import SyncFilesystem, PathNotFoundError, FileEncodeError


def test_ensure_dir_creates_directory(
    tmp_path: Path, sync_filesystem: SyncFilesystem
) -> None:
    """It should ensure a directory exists."""
    path = tmp_path / "foo"

    sync_filesystem.ensure_dir(path)
    assert path.is_dir() is True

    # ensure that subsequent calls do not error
    sync_filesystem.ensure_dir(path)
    assert path.is_dir() is True


def test_remove_deletes_file(tmp_path: Path, sync_filesystem: SyncFilesystem) -> None:
    """It should delete a given file."""
    path = tmp_path / "foo"
    path.with_suffix(".json").touch()

    sync_filesystem.remove(path)

    assert path.exists() is False


def test_remove_raises_if_no_file(
    tmp_path: Path, sync_filesystem: SyncFilesystem
) -> None:
    """It should raise a PathNotFoundError error if file to remove isn't found."""
    path = tmp_path / "foo"

    with pytest.raises(PathNotFoundError):
        sync_filesystem.remove(path)


def test_remove_dir_deletes_tree(
    tmp_path: Path, sync_filesystem: SyncFilesystem
) -> None:
    """It should delete a directory and all files in it."""
    (tmp_path / "foo.json").touch()
    (tmp_path / "bar.json").touch()
    (tmp_path / "baz.json").touch()

    sync_filesystem.remove_dir(tmp_path)

    assert tmp_path.exists() is False


def test_write_json_encodes_and_writes_obj(
    tmp_path: Path, sync_filesystem: SyncFilesystem
) -> None:
    """It should encode and write a JSON object to a file."""
    path = tmp_path / "foo"
    sync_filesystem.write_json(path, {"foo": "hello", "bar": 0})

    assert path.with_suffix(".json").read_text() == """{"foo": "hello", "bar": 0}"""


def test_write_json_raises_encode_error(
    tmp_path: Path, sync_filesystem: SyncFilesystem
) -> None:
    """It should raise a FileEncodeError if object cannot be encoded to JSON."""
    path = tmp_path / "foo"

    with pytest.raises(FileEncodeError, match="ellipsis is not JSON serializable"):
        sync_filesystem.write_json(path, {"nope": ...})


def test_write_json_with_custom_encoder(
    tmp_path: Path, mock_encode_json: MagicMock, sync_filesystem: SyncFilesystem
) -> None:
    """It should encode and write a file using a custom encoder."""
    path = tmp_path / "foo"
    obj = {"foo": "hello", "bar": 0}
    mock_encode_json.return_value = "I just met you"

    sync_filesystem.write_json(path, obj, encode_json=mock_encode_json)

    assert path.with_suffix(".json").read_text() == "I just met you"
    mock_encode_json.assert_called_with(obj)


def test_write_json_when_custom_encoder_raises(
    tmp_path: Path, mock_encode_json: MagicMock, sync_filesystem: SyncFilesystem
) -> None:
    """It should raise a FileEncodeError if the custom encoder raises."""
    path = tmp_path / "foo"
    obj = {"foo": "hello", "bar": 0}
    mock_encode_json.side_effect = Exception("oh no")

    with pytest.raises(FileEncodeError, match="oh no"):
        sync_filesystem.write_json(path, obj, encode_json=mock_encode_json)
