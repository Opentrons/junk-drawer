"""Integration tests for AsyncFilesystem read operations."""
import pytest
from mock import MagicMock
from pathlib import Path
from junk_drawer.filesystem import AsyncFilesystem, PathNotFoundError, FileEncodeError

pytestmark = pytest.mark.asyncio


async def test_remove_deletes_file(tmp_path: Path, filesystem: AsyncFilesystem) -> None:
    """It should delete a given file."""
    path = tmp_path / "foo"
    path.with_suffix(".json").touch()

    await filesystem.remove(path)

    assert path.exists() is False


async def test_remove_raises_if_no_file(
    tmp_path: Path, filesystem: AsyncFilesystem
) -> None:
    """It should raise a PathNotFoundError error if file to remove isn't found."""
    path = tmp_path / "foo"

    with pytest.raises(PathNotFoundError):
        await filesystem.remove(path)


async def test_remove_dir_deletes_tree(
    tmp_path: Path, filesystem: AsyncFilesystem
) -> None:
    """It should delete a directory and all files in it."""
    (tmp_path / "foo.json").touch()
    (tmp_path / "bar.json").touch()
    (tmp_path / "baz.json").touch()

    await filesystem.remove_dir(tmp_path)

    assert tmp_path.exists() is False


async def test_write_json_enocdes_and_writes_obj(
    tmp_path: Path, filesystem: AsyncFilesystem
) -> None:
    """It should encode and write a JSON object to a file."""
    path = tmp_path / "foo"
    await filesystem.write_json(path, {"foo": "hello", "bar": 0})

    assert path.with_suffix(".json").read_text() == """{"foo": "hello", "bar": 0}"""


async def test_write_json_raises_encode_error(
    tmp_path: Path, filesystem: AsyncFilesystem
) -> None:
    """It should raise a FileEncodeError if object cannot be encoded to JSON."""
    path = tmp_path / "foo"

    with pytest.raises(FileEncodeError, match="ellipsis is not JSON serializable"):
        await filesystem.write_json(path, {"nope": ...})


async def test_write_json_with_custom_encoder(
    tmp_path: Path, mock_encode_json: MagicMock, filesystem: AsyncFilesystem
) -> None:
    """It should encode and write a file using a custom encoder."""
    path = tmp_path / "foo"
    obj = {"foo": "hello", "bar": 0}
    mock_encode_json.return_value = "I just met you"

    await filesystem.write_json(path, obj, encode_json=mock_encode_json)

    assert path.with_suffix(".json").read_text() == "I just met you"
    mock_encode_json.assert_called_with(obj)


async def test_write_json_when_custom_encoder_raises(
    tmp_path: Path, mock_encode_json: MagicMock, filesystem: AsyncFilesystem
) -> None:
    """It should raise a FileEncodeError if the custom encoder raises."""
    path = tmp_path / "foo"
    obj = {"foo": "hello", "bar": 0}
    mock_encode_json.side_effect = Exception("oh no")

    with pytest.raises(FileEncodeError, match="oh no"):
        await filesystem.write_json(path, obj, encode_json=mock_encode_json)
