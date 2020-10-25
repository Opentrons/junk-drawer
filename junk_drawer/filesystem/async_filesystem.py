"""Async threadpool-based JSON filesystem."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from logging import getLogger
from pathlib import Path, PurePath
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
    AsyncFilesystemLike,
    ResultT,
    JSONParser,
    JSONEncoder,
    DirectoryEntry,
)


log = getLogger(__name__)


class AsyncFilesystem(AsyncFilesystemLike):
    """
    Default async threadpool JSON filesystem adapter.

    File I/O and JSON (de)serialization will happen in a threads using the
    asyncio event loop's default ThreadPoolExecutor.
    """

    def __init__(self, executor: Optional[ThreadPoolExecutor] = None) -> None:
        """Initialize an AsyncFilesystem adapter."""
        self._loop = asyncio.get_event_loop()
        self._executor = executor

    async def ensure_dir(self, path: PurePath) -> PurePath:
        """Ensure a directory at `path` exists, creating it if it doesn't."""
        real_path = Path(path)
        task = partial(real_path.mkdir, parents=True, exist_ok=True)

        await self._loop.run_in_executor(self._executor, task)

        return path

    async def read_dir(self, path: PurePath) -> List[str]:
        """Get the stem names of all JSON files in the directory."""
        real_path = Path(path)
        children = await self._loop.run_in_executor(self._executor, real_path.iterdir)

        return [
            child.stem
            for child in children
            if child.suffix == ".json" and not child.name.startswith(".")
        ]

    async def file_exists(self, path: PurePath) -> bool:
        """Return True if `{path}.json` is a file."""
        real_path = Path(path.with_suffix(".json"))
        task = real_path.is_file
        exists = await self._loop.run_in_executor(self._executor, task)

        return exists

    async def read_json(
        self,
        path: PurePath,
        parse_json: JSONParser[ResultT] = default_parse_json,
    ) -> ResultT:
        """Read and parse a single JSON file."""

        def _read_and_parse() -> ResultT:
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

        return await self._loop.run_in_executor(self._executor, _read_and_parse)

    async def read_json_dir(
        self,
        path: PurePath,
        parse_json: JSONParser[ResultT] = default_parse_json,
        ignore_errors: bool = False,
    ) -> List[DirectoryEntry[ResultT]]:
        """Read and parse all JSON files in a directory concurrently."""

        async def _read_entry(child: str) -> DirectoryEntry[ResultT]:
            child_path = path / child
            child_contents = await self.read_json(child_path, parse_json)
            return DirectoryEntry(path=child_path, contents=child_contents)

        children = await self.read_dir(path)
        tasks = [_read_entry(child) for child in children]
        entries = await asyncio.gather(*tasks, return_exceptions=ignore_errors)

        if ignore_errors:
            entries = [entry for entry in entries if not isinstance(entry, Exception)]

        return entries

    async def write_json(
        self,
        path: PurePath,
        contents: ResultT,
        encode_json: JSONEncoder[ResultT] = default_encode_json,
    ) -> None:
        """Write an object to a JSON file."""
        file_path = Path(path.with_suffix(".json"))

        def _encode_and_write() -> None:
            try:
                encoded_contents = encode_json(contents)
            except Exception as error:
                log.debug(f"Unexpected error encoding for {file_path}", exc_info=error)
                raise FileEncodeError(str(error)) from error

            try:
                file_path.write_text(encoded_contents)
            except Exception as error:
                # NOTE: this except branch is not covered by tests, but is important
                log.debug(f"Unexpected error writing to {file_path}", exc_info=error)
                raise FileWriteError(str(error)) from error

        await self._loop.run_in_executor(self._executor, _encode_and_write)

        return None

    async def remove(self, path: PurePath) -> None:
        """Delete a JSON file."""
        file_path = Path(path.with_suffix(".json"))

        try:
            await self._loop.run_in_executor(self._executor, file_path.unlink)
        except FileNotFoundError as error:
            raise PathNotFoundError(str(error)) from error
        except Exception as error:
            # NOTE: this except branch is not covered by tests, but is important
            log.debug(f"Unexpected error reading {file_path}", exc_info=error)
            raise FileRemoveError(str(error)) from error

        return None

    async def remove_dir(self, path: PurePath) -> None:
        """Delete all files in the given directory and the directory."""
        task = partial(rmtree, path=path)

        await self._loop.run_in_executor(self._executor, task)

        return None
