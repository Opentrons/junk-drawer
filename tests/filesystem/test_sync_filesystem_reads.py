"""Integration tests for AsyncFilesystem read operations."""
import pytest
from mock import MagicMock
from pathlib import Path, PurePosixPath
from typing import Any, Dict, List

from junk_drawer.filesystem import (
    SyncFilesystem,
    DirectoryEntry as Entry,
    PathNotFoundError,
    FileParseError,
)

ParsedObj = Dict[str, Any]


def test_ensure_dir_noops_when_dir_exists(
    tmp_path: Path, sync_filesystem: SyncFilesystem
) -> None:
    """It should do nothing with ensure_dir if the directory already exists."""
    tmp_path.mkdir(exist_ok=True)
    dir_name = PurePosixPath(tmp_path)
    result = sync_filesystem.ensure_dir(dir_name)

    assert dir_name == result


def test_ensure_dir_creates_dir(
    tmp_path: Path, sync_filesystem: SyncFilesystem
) -> None:
    """It should create a directory with ensure_dir if it doesn't exist."""
    dir_name = PurePosixPath(tmp_path) / "the_limit_does_not_exist"
    result = sync_filesystem.ensure_dir(dir_name)

    assert result == dir_name
    assert Path(dir_name).is_dir()


def test_read_dir_with_empty_dir(
    tmp_path: Path, sync_filesystem: SyncFilesystem
) -> None:
    """It should return an empty list with read_dir on an empty directory."""
    basenames = sync_filesystem.read_dir(tmp_path)

    assert basenames == []


def test_read_dir_with_dir_of_json_files(
    tmp_path: Path, sync_filesystem: SyncFilesystem
) -> None:
    """It should return a list of JSON basenames with read_dir."""
    (tmp_path / "foo.json").touch()
    (tmp_path / "bar.json").touch()
    (tmp_path / "baz.json").touch()
    basenames = sync_filesystem.read_dir(tmp_path)

    assert set(basenames) == set(["foo", "bar", "baz"])


def test_read_dir_ignores_non_json_and_dotfiles(
    tmp_path: Path, sync_filesystem: SyncFilesystem
) -> None:
    """It should ignore dotfiles and non-JSON files with read_dir."""
    (tmp_path / "foo.json").touch()
    (tmp_path / ".bar.json").touch()
    (tmp_path / "baz.zip").touch()
    basenames = sync_filesystem.read_dir(tmp_path)

    assert basenames == ["foo"]


def test_read_dir_walks_directories(
    tmp_path: Path, sync_filesystem: SyncFilesystem
) -> None:
    """It should ignore include files nested in directories in read_dir."""
    (tmp_path / "foo.json").touch()
    (tmp_path / "bar").mkdir()
    (tmp_path / "bar" / "baz.json").touch()
    basenames = sync_filesystem.read_dir(tmp_path)

    assert basenames == ["foo", "bar/baz"]


def test_file_exists_returns_false_if_no_file(
    tmp_path: Path, sync_filesystem: SyncFilesystem
) -> None:
    """It should return False with file_exists if no JSON files exist."""
    path = PurePosixPath(tmp_path / "foo")
    exists = sync_filesystem.file_exists(path)

    assert exists is False


def test_file_exists_returns_true_if_file_exists(
    tmp_path: Path, sync_filesystem: SyncFilesystem
) -> None:
    """It should return True with file_exists if JSON file exists."""
    (tmp_path / "foo.json").touch()
    path = PurePosixPath(tmp_path / "foo")
    exists = sync_filesystem.file_exists(path)

    assert exists is True


def test_file_exists_returns_false_if_path_is_directory(
    tmp_path: Path, sync_filesystem: SyncFilesystem
) -> None:
    """It should return False with file_exists if path points to directory."""
    (tmp_path / "foo.json").mkdir()
    path = PurePosixPath(tmp_path / "foo")
    exists = sync_filesystem.file_exists(path)

    assert exists is False


def test_read_json_loads_json_file_to_dict(
    tmp_path: Path, sync_filesystem: SyncFilesystem
) -> None:
    """It should read a file and load the contents into JSON."""
    Path(tmp_path / "foo.json").write_text("""{ "foo": "hello", "bar": 42 }""")

    path = PurePosixPath(tmp_path / "foo")
    result: ParsedObj = sync_filesystem.read_json(path)

    assert result == {"foo": "hello", "bar": 42}


def test_read_json_raises_path_does_not_exist_error(
    tmp_path: Path, sync_filesystem: SyncFilesystem
) -> None:
    """It should return a FileNotFoundError if file doesn't exist."""
    path = PurePosixPath(tmp_path / "foo")

    with pytest.raises(PathNotFoundError, match="No such file or directory"):
        sync_filesystem.read_json(path)


def test_read_json_raises_parse_error(
    tmp_path: Path, sync_filesystem: SyncFilesystem
) -> None:
    """It should raise a FileParseError if file is not valid JSON."""
    Path(tmp_path / "foo.json").write_text("""{ "foo": "hello", }""")

    path = PurePosixPath(tmp_path / "foo")

    with pytest.raises(FileParseError, match="Expecting property name"):
        sync_filesystem.read_json(path)


def test_read_json_dir_reads_multiple_files(
    tmp_path: Path, sync_filesystem: SyncFilesystem
) -> None:
    """It should read a all files in a directory."""
    Path(tmp_path / "foo.json").write_text("""{ "foo": "hello", "bar": 0 }""")
    Path(tmp_path / "bar.json").write_text("""{ "foo": "from the", "bar": 1 }""")
    Path(tmp_path / "baz.json").write_text("""{ "foo": "other side", "bar": 2 }""")

    path = PurePosixPath(tmp_path)
    files: List[Entry[ParsedObj]] = sync_filesystem.read_json_dir(path)

    assert len(files) == 3
    assert Entry(path=path / "foo", contents={"foo": "hello", "bar": 0}) in files
    assert Entry(path=path / "bar", contents={"foo": "from the", "bar": 1}) in files
    assert Entry(path=path / "baz", contents={"foo": "other side", "bar": 2}) in files


def test_read_json_dir_reads_multiple_files_nested(
    tmp_path: Path, sync_filesystem: SyncFilesystem
) -> None:
    """It should read a all nested files in a directory."""
    Path(tmp_path / "some-dir").mkdir()
    Path(tmp_path / "some-dir" / "foo.json").write_text(
        """{ "foo": "hello", "bar": 0 }"""
    )
    Path(tmp_path / "bar.json").write_text("""{ "foo": "from the", "bar": 1 }""")

    path = PurePosixPath(tmp_path)
    files: List[Entry[ParsedObj]] = sync_filesystem.read_json_dir(path)

    assert len(files) == 2
    assert (
        Entry(path=path / "some-dir" / "foo", contents={"foo": "hello", "bar": 0})
        in files
    )
    assert Entry(path=path / "bar", contents={"foo": "from the", "bar": 1}) in files


def test_read_json_dir_can_ignore_errors(
    tmp_path: Path, sync_filesystem: SyncFilesystem
) -> None:
    """It should allow reading all directory files while ignoring any errors."""
    Path(tmp_path / "foo.json").write_text("""{ "foo": "hello", "bar": 0 }""")
    Path(tmp_path / "bar.json").write_text("""{ "foo": "from the",}""")

    path = PurePosixPath(tmp_path)
    files: List[Entry[ParsedObj]] = sync_filesystem.read_json_dir(
        path, ignore_errors=True
    )

    assert files == [Entry(path=path / "foo", contents={"foo": "hello", "bar": 0})]


def test_read_json_with_custom_parser(
    tmp_path: Path, mock_parse_json: MagicMock, sync_filesystem: SyncFilesystem
) -> None:
    """It should read a file and parse into JSON using custom parser."""
    Path(tmp_path / "foo.json").write_text("""{ "this": "is crazy" }""")

    mock_parse_json.return_value = {"call me": "maybe"}
    path = PurePosixPath(tmp_path / "foo")
    result = sync_filesystem.read_json(path, parse_json=mock_parse_json)

    assert result == {"call me": "maybe"}
    mock_parse_json.assert_called_with("""{ "this": "is crazy" }""")


def test_read_json_when_custom_parser_raises(
    tmp_path: Path, mock_parse_json: MagicMock, sync_filesystem: SyncFilesystem
) -> None:
    """It should raise a FileParseError if the custom parser raises."""
    Path(tmp_path / "foo.json").write_text("""{ "foo": "hello", "bar": 42 }""")

    error = Exception("oh no")
    mock_parse_json.side_effect = error
    path = PurePosixPath(tmp_path / "foo")

    with pytest.raises(FileParseError):
        sync_filesystem.read_json(path, parse_json=mock_parse_json)


def test_read_json_dir_with_custom_parser(
    tmp_path: Path, mock_parse_json: MagicMock, sync_filesystem: SyncFilesystem
) -> None:
    """It should read a all files in a directory."""
    Path(tmp_path / "foo.json").write_text("""{ "foo": "hello", "bar": 0 }""")
    Path(tmp_path / "bar.json").write_text("""{ "foo": "from the", "bar": 1 }""")
    Path(tmp_path / "baz.json").write_text("""{ "foo": "other side", "bar": 2 }""")

    mock_parse_json.return_value = {"call me": "maybe"}
    path = PurePosixPath(tmp_path)
    files = sync_filesystem.read_json_dir(path, parse_json=mock_parse_json)

    assert len(files) == 3
    assert Entry(path=path / "foo", contents={"call me": "maybe"}) in files
    assert Entry(path=path / "bar", contents={"call me": "maybe"}) in files
    assert Entry(path=path / "baz", contents={"call me": "maybe"}) in files
    mock_parse_json.assert_any_call("""{ "foo": "hello", "bar": 0 }""")
    mock_parse_json.assert_any_call("""{ "foo": "from the", "bar": 1 }""")
    mock_parse_json.assert_any_call("""{ "foo": "other side", "bar": 2 }""")
