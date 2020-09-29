"""Base filesystem adapter interfaces."""
from abc import ABC
from typing import List, Tuple
from pathlib import PurePath


class AsyncFilesystemLike(ABC):
    """Abstract asynchronous filesystem interface."""

    async def ensure_dir(self, path: PurePath) -> PurePath:
        """Ensure a directory at `path` exists, creating it if it doesn't."""
        ...

    async def read_dir(self, path: PurePath) -> List[str]:
        """Get the extensionless basenames of all JSON files in the directory."""
        ...

    async def file_exists(self, path: PurePath) -> bool:
        """Return True if `{path}.json` is a file."""
        ...

    async def read_json(self, path: PurePath) -> dict:
        """Read and parse a single JSON file."""
        ...

    async def read_json_dir(self, path: PurePath) -> List[Tuple[str, dict]]:
        """Read and parse all JSON files in a directory concurrently."""
        ...
