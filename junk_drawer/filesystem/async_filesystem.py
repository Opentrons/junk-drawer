"""Async threadpool-based JSON filesystem."""
import asyncio
from functools import partial
from logging import getLogger
from pathlib import Path, PurePath
from typing import List

from .errors import PathNotFoundError, FileReadError, FileParseError
from .base import (
    default_parse_json,
    AsyncFilesystemLike,
    ResultT,
    JSONParser,
    DirectoryEntry,
)


log = getLogger(__name__)


class AsyncFilesystem(AsyncFilesystemLike):
    """
    Default async threadpool JSON filesystem adapter.

    File I/O and JSON (de)serialization will happen in a threads using the
    asyncio event loop's default ThreadPoolExecutor.
    """

    def __init__(self) -> None:
        """Initialize an AsyncFilesystem adapter."""
        self._loop = asyncio.get_event_loop()

    async def ensure_dir(self, path: PurePath) -> PurePath:
        """Ensure a directory at `path` exists, creating it if it doesn't."""
        real_path = Path(path)
        task = partial(real_path.mkdir, parents=True, exist_ok=True)
        await self._loop.run_in_executor(None, task)
        return path

    async def read_dir(self, path: PurePath) -> List[str]:
        """Get the stem names of all JSON files in the directory."""
        real_path = Path(path)
        task = real_path.iterdir
        children = await self._loop.run_in_executor(None, task)
        return [
            child.stem
            for child in children
            if child.suffix == ".json" and not child.name.startswith(".")
        ]

    async def file_exists(self, path: PurePath) -> bool:
        """Return True if `{path}.json` is a file."""
        real_path = Path(path.with_suffix(".json"))
        task = real_path.is_file
        exists = await self._loop.run_in_executor(None, task)

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
            except FileNotFoundError as not_found_error:
                raise PathNotFoundError() from not_found_error
            except Exception as read_error:
                # NOTE(mc, 2020-10-03): this condition is not covered by tests
                msg = "Unexpected error reading {file_path}"
                log.debug(msg, exc_info=read_error)
                raise FileReadError(msg) from read_error

            try:
                result = parse_json(text)
            except Exception as parse_error:
                # this should only happen if the file being read has been modified
                # outside of this library or a defective custom JSON encoder was used
                msg = f"Unexpected error parsing {file_path}"
                log.debug(msg, exc_info=parse_error)
                raise FileParseError(msg) from parse_error

            return result

        return await self._loop.run_in_executor(None, _read_and_parse)

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
