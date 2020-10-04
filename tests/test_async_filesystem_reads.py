"""Integration tests for AsyncFilesystem read operations."""
import pytest
from pathlib import Path, PurePath
from junk_drawer.filesystem import (
    AsyncFilesystem,
    DirectoryEntry as Entry,
    PathNotFoundError,
    FileParseError,
)

pytestmark = pytest.mark.asyncio


@pytest.fixture
def filesystem():
    """Create a fresh filesystem adapter for every test."""
    return AsyncFilesystem()


async def test_ensure_dir_noops_when_dir_exists(tmp_path, filesystem):
    """It should do nothing with ensure_dir if the directory already exists."""
    tmp_path.mkdir(exist_ok=True)
    dir_name = PurePath(tmp_path)
    result = await filesystem.ensure_dir(dir_name)

    assert dir_name == result


async def test_ensure_dir_creates_dir(tmp_path, filesystem):
    """It should create a directory with ensure_dir if it doesn't exist."""
    dir_name = PurePath(tmp_path) / "the_limit_does_not_exist"
    result = await filesystem.ensure_dir(dir_name)

    assert result == dir_name
    assert Path(dir_name).is_dir()


async def test_read_dir_with_empty_dir(tmp_path, filesystem):
    """It should return an empty list with read_dir on an empty directory."""
    basenames = await filesystem.read_dir(tmp_path)

    assert basenames == []


async def test_read_dir_with_dir_of_json_files(tmp_path, filesystem):
    """It should return a list oj JSON basenames with read_dir."""
    (tmp_path / "foo.json").touch()
    (tmp_path / "bar.json").touch()
    (tmp_path / "baz.json").touch()
    basenames = await filesystem.read_dir(tmp_path)

    assert set(basenames) == set(["foo", "bar", "baz"])


async def test_read_dir_ignores_non_json_and_dotfiles(tmp_path, filesystem):
    """It should ignore dotfiles and non-JSON files with read_dir."""
    (tmp_path / "foo.json").touch()
    (tmp_path / ".bar.json").touch()
    (tmp_path / "baz.zip").touch()
    basenames = await filesystem.read_dir(tmp_path)

    assert basenames == ["foo"]


async def test_file_exists_returns_false_if_no_file(tmp_path, filesystem):
    """It should return False with file_exists if no JSON files exist."""
    path = PurePath(tmp_path / "foo")
    exists = await filesystem.file_exists(path)

    assert exists is False


async def test_file_exists_returns_true_if_file_exists(tmp_path, filesystem):
    """It should return True with file_exists if JSON file exists."""
    (tmp_path / "foo.json").touch()
    path = PurePath(tmp_path / "foo")
    exists = await filesystem.file_exists(path)

    assert exists is True


async def test_file_exists_returns_false_if_path_is_directory(tmp_path, filesystem):
    """It should return False with file_exists if path points to directory."""
    (tmp_path / "foo.json").mkdir()
    path = PurePath(tmp_path / "foo")
    exists = await filesystem.file_exists(path)

    assert exists is False


async def test_read_json_loads_json_file_to_dict(tmp_path, filesystem):
    """It should read a file and load the contents into JSON."""
    Path(tmp_path / "foo.json").write_text("""{ "foo": "hello", "bar": 42 }""")

    path = PurePath(tmp_path / "foo")
    result = await filesystem.read_json(path)

    assert result == {"foo": "hello", "bar": 42}


async def test_read_json_raises_path_does_not_exist_error(tmp_path, filesystem):
    """It should return a FileNotFoundError if file doesn't exist."""
    path = PurePath(tmp_path / "foo")

    with pytest.raises(PathNotFoundError, match="No such file or directory"):
        await filesystem.read_json(path)


async def test_read_json_raises_parse_error(tmp_path, filesystem):
    """It should raise a FileParseError if file is not valid JSON."""
    Path(tmp_path / "foo.json").write_text("""{ "foo": "hello", }""")

    path = PurePath(tmp_path / "foo")

    with pytest.raises(FileParseError, match="Expecting property name"):
        await filesystem.read_json(path)


async def test_read_json_dir_reads_multiple_files(tmp_path, filesystem):
    """It should read a all files in a directory."""
    Path(tmp_path / "foo.json").write_text("""{ "foo": "hello", "bar": 0 }""")
    Path(tmp_path / "bar.json").write_text("""{ "foo": "from the", "bar": 1 }""")
    Path(tmp_path / "baz.json").write_text("""{ "foo": "other side", "bar": 2 }""")

    path = PurePath(tmp_path)
    files = await filesystem.read_json_dir(path)

    assert len(files) == 3
    assert Entry(path=path / "foo", contents={"foo": "hello", "bar": 0}) in files
    assert Entry(path=path / "bar", contents={"foo": "from the", "bar": 1}) in files
    assert Entry(path=path / "baz", contents={"foo": "other side", "bar": 2}) in files


async def test_read_json_dir_can_ignore_errors(tmp_path, filesystem):
    """It should allow reading all directory files while ignoring any errors."""
    Path(tmp_path / "foo.json").write_text("""{ "foo": "hello", "bar": 0 }""")
    Path(tmp_path / "bar.json").write_text("""{ "foo": "from the",}""")

    path = PurePath(tmp_path)
    files = await filesystem.read_json_dir(path, ignore_errors=True)

    assert files == [Entry(path=path / "foo", contents={"foo": "hello", "bar": 0})]
