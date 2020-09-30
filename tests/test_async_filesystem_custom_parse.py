"""Integration tests for AsyncFilesystem reads with custom parsing."""
import pytest
from mock import MagicMock
from pathlib import Path, PurePath
from junk_drawer.filesystem import AsyncFilesystem, DirectoryEntry, FileParseError

pytestmark = pytest.mark.asyncio


@pytest.fixture
def parse_json():
    """Mock parse JSON function."""
    return MagicMock()


@pytest.fixture
def filesystem(parse_json):
    """Create a fresh filesystem adapter for every test."""
    return AsyncFilesystem()


async def test_read_json_with_custom_parser(tmp_path, parse_json, filesystem):
    """It should read a file and parse into JSON using custom parser."""
    Path(tmp_path / "foo.json").write_text("""{ "this": "is crazy" }""")

    parse_json.return_value = {"call me": "maybe"}
    path = PurePath(tmp_path / "foo")
    result = await filesystem.read_json(path, parse_json=parse_json)

    assert result == {"call me": "maybe"}
    parse_json.assert_called_with("""{ "this": "is crazy" }""")


async def test_read_json_when_custom_parser_raises(tmp_path, parse_json, filesystem):
    """It should raise a FileParseError if the custom parser raises."""
    Path(tmp_path / "foo.json").write_text("""{ "foo": "hello", "bar": 42 }""")

    error = Exception("oh no")
    parse_json.side_effect = error
    path = PurePath(tmp_path / "foo")

    with pytest.raises(FileParseError):
        await filesystem.read_json(path, parse_json=parse_json)


async def test_read_json_dir_with_custom_parser(tmp_path, parse_json, filesystem):
    """It should read a all files in a directory."""
    Path(tmp_path / "foo.json").write_text("""{ "foo": "hello", "bar": 0 }""")
    Path(tmp_path / "bar.json").write_text("""{ "foo": "from the", "bar": 1 }""")
    Path(tmp_path / "baz.json").write_text("""{ "foo": "other side", "bar": 2 }""")

    parse_json.return_value = {"call me": "maybe"}
    path = PurePath(tmp_path)
    files = await filesystem.read_json_dir(path, parse_json=parse_json)

    assert len(files) == 3
    assert DirectoryEntry(path=path / "foo", contents={"call me": "maybe"}) in files
    assert DirectoryEntry(path=path / "bar", contents={"call me": "maybe"}) in files
    assert DirectoryEntry(path=path / "baz", contents={"call me": "maybe"}) in files
    parse_json.assert_any_call("""{ "foo": "hello", "bar": 0 }""")
    parse_json.assert_any_call("""{ "foo": "from the", "bar": 1 }""")
    parse_json.assert_any_call("""{ "foo": "other side", "bar": 2 }""")
