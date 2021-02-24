"""Async threadpool-based JSON filesystem."""
from __future__ import annotations
from asyncio import get_event_loop, gather, AbstractEventLoop
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from pathlib import PurePath, PurePosixPath
from typing import List, Optional

from .base import (
    default_parse_json,
    default_encode_json,
    AsyncFilesystemLike,
    ResultT,
    JSONParser,
    JSONEncoder,
    DirectoryEntry,
)

from .sync_filesystem import SyncFilesystem


class AsyncFilesystem(AsyncFilesystemLike):
    """
    Default async threadpool JSON filesystem adapter.

    File I/O and JSON (de)serialization will happen in a threads using the
    asyncio event loop's default ThreadPoolExecutor.
    """

    _sync_filesystem: SyncFilesystem
    _executor: Optional[ThreadPoolExecutor]

    @classmethod
    def create(
        cls,
        executor: Optional[ThreadPoolExecutor] = None,
    ) -> AsyncFilesystem:
        """Create an AsyncFilesystem with backing synchronous logic."""
        return cls(
            sync_filesystem=SyncFilesystem(),
            executor=executor,
        )

    def __init__(
        self,
        sync_filesystem: SyncFilesystem,
        executor: Optional[ThreadPoolExecutor] = None,
    ) -> None:
        """Initialize an AsyncFilesystem adapter."""
        self._sync_filesystem = sync_filesystem
        self._executor = executor

    @property
    def _loop(self) -> AbstractEventLoop:
        return get_event_loop()

    @property
    def sync(self) -> SyncFilesystem:
        """Get the underlying synchronous filesystem interface."""
        return self._sync_filesystem

    async def ensure_dir(self, path: PurePath) -> PurePath:
        """Ensure a directory at `path` exists, creating it if it doesn't."""
        task = partial(self.sync.ensure_dir, path=path)
        await self._loop.run_in_executor(self._executor, task)
        return path

    async def read_dir(self, path: PurePath) -> List[str]:
        """Get the stem names of all JSON files in the directory."""
        task = partial(self.sync.read_dir, path=path)
        return await self._loop.run_in_executor(self._executor, task)

    async def file_exists(self, path: PurePath) -> bool:
        """Return True if `{path}.json` is a file."""
        task = partial(self.sync.file_exists, path=path)
        return await self._loop.run_in_executor(self._executor, task)

    async def read_json(
        self,
        path: PurePath,
        parse_json: JSONParser[ResultT] = default_parse_json,
    ) -> ResultT:
        """Read and parse a single JSON file."""
        task: partial[ResultT] = partial(
            self.sync.read_json, path=path, parse_json=parse_json
        )

        return await self._loop.run_in_executor(self._executor, task)

    async def read_json_dir(
        self,
        path: PurePath,
        parse_json: JSONParser[ResultT] = default_parse_json,
        ignore_errors: bool = False,
    ) -> List[DirectoryEntry[ResultT]]:
        """Read and parse all JSON files in a directory concurrently."""

        async def _read_entry(child: str) -> DirectoryEntry[ResultT]:
            child_path = PurePosixPath(path / child)
            child_contents = await self.read_json(child_path, parse_json)
            return DirectoryEntry(path=child_path, contents=child_contents)

        children = await self.read_dir(path)
        tasks = [_read_entry(child) for child in children]
        entries = await gather(*tasks, return_exceptions=ignore_errors)

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
        task = partial(
            self.sync.write_json, path=path, contents=contents, encode_json=encode_json
        )

        return await self._loop.run_in_executor(self._executor, task)

    async def remove(self, path: PurePath) -> None:
        """Delete a JSON file."""
        task = partial(self.sync.remove, path=path)

        return await self._loop.run_in_executor(self._executor, task)

    async def remove_dir(self, path: PurePath) -> None:
        """Delete all files in the given directory and the directory."""
        task = partial(self.sync.remove_dir, path=path)

        return await self._loop.run_in_executor(self._executor, task)
