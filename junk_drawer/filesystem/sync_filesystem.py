"""Synchronous JSON filesystem."""
from logging import getLogger
from pathlib import Path, PurePath, PurePosixPath
from shutil import rmtree
from typing import List, Optional

from .errors import (
    PathNotFoundError,
    FileReadError,
    FileWriteError,
    FileParseError,
    FileEncodeError,
    FileRemoveError,
)

from .base import (
    default_parse_json,
    default_encode_json,
    ResultT,
    JSONParser,
    JSONEncoder,
    DirectoryEntry,
    SyncFilesystemLike,
)


log = getLogger(__name__)


class SyncFilesystem(SyncFilesystemLike):
    """Synchronous JSON filesystem adapter."""

    def ensure_dir(self, path: PurePath) -> PurePath:
        """Ensure a directory at `path` exists, creating it if it doesn't."""
        Path(path).mkdir(parents=True, exist_ok=True)
        return path

    def read_dir(self, path: PurePath) -> List[str]:
        """Get the stem names of all JSON files in the directory."""
        file_paths = Path(path).glob("**/*.json")

        return [
            str(file_path.relative_to(path).with_suffix("").as_posix())
            for file_path in file_paths
            if not file_path.stem.startswith(".")
        ]

    def file_exists(self, path: PurePath) -> bool:
        """Return True if `{path}.json` is a file."""
        return Path(path.with_suffix(".json")).is_file()

    def read_json(
        self,
        path: PurePath,
        parse_json: JSONParser[ResultT] = default_parse_json,
    ) -> ResultT:
        """Read and parse a single JSON file."""
        file_path = Path(path).with_suffix(".json")

        try:
            text = file_path.read_text()
        except FileNotFoundError as error:
            raise PathNotFoundError(str(error)) from error
        except Exception as error:
            # NOTE: this except branch is not covered by tests, but is important
            log.debug(f"Unexpected error reading {file_path}", exc_info=error)
            raise FileReadError(str(error)) from error

        try:
            result = parse_json(text)
        except Exception as error:
            # this should only happen if the file being read has been modified
            # outside of this library or a defective custom JSON encoder was used
            log.debug(f"Unexpected error parsing {file_path}", exc_info=error)
            raise FileParseError(str(error)) from error

        return result

    def read_json_dir(
        self,
        path: PurePath,
        parse_json: JSONParser[ResultT] = default_parse_json,
        ignore_errors: bool = False,
    ) -> List[DirectoryEntry[ResultT]]:
        """Read and parse all JSON files in a directory serially."""

        def _read_entry(child: str) -> Optional[DirectoryEntry[ResultT]]:
            child_path = PurePosixPath(path / child)

            try:
                child_contents = self.read_json(child_path, parse_json)
                return DirectoryEntry(path=child_path, contents=child_contents)
            except Exception as error:
                if not ignore_errors:
                    raise error

                return None

        children = self.read_dir(path)
        entries = [_read_entry(child) for child in children]

        return [ent for ent in entries if ent is not None]

    def write_json(
        self,
        path: PurePath,
        contents: ResultT,
        encode_json: JSONEncoder[ResultT] = default_encode_json,
    ) -> None:
        """Write an object to a JSON file."""
        file_path = Path(path.with_suffix(".json"))

        try:
            encoded_contents = encode_json(contents)
        except Exception as error:
            log.debug(f"Unexpected error encoding for {file_path}", exc_info=error)
            raise FileEncodeError(str(error)) from error

        try:
            self.ensure_dir(file_path.parent)
            file_path.write_text(encoded_contents)
        except Exception as error:
            # NOTE: this except branch is not covered by tests, but is important
            log.debug(f"Unexpected error writing to {file_path}", exc_info=error)
            raise FileWriteError(str(error)) from error

        return None

    def remove(self, path: PurePath) -> None:
        """Delete a JSON file."""
        file_path = Path(path.with_suffix(".json"))

        try:
            file_path.unlink()
        except FileNotFoundError as error:
            raise PathNotFoundError(str(error)) from error
        except Exception as error:
            # NOTE: this except branch is not covered by tests, but is important
            log.debug(f"Unexpected error reading {file_path}", exc_info=error)
            raise FileRemoveError(str(error)) from error

        return None

    def remove_dir(self, path: PurePath) -> None:
        """Delete all files in the given directory and the directory."""
        rmtree(path=path)

        return None
