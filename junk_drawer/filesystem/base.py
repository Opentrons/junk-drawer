"""Base filesystem adapter interfaces."""
from abc import ABC
from dataclasses import dataclass
from json import loads as json_loads
from pathlib import PurePath
from typing import Any, Callable, Generic, List, TypeVar


ResultT = TypeVar("ResultT")


@dataclass
class DirectoryEntry(Generic[ResultT]):
    """Filename and parsed file contents from a full directory read."""

    path: PurePath
    contents: ResultT


JSONParser = Callable[[str], ResultT]


def default_parse_json(text: str) -> Any:
    """Parse a JSON string using builtin json module."""
    return json_loads(text)


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

    async def read_json(
        self,
        path: PurePath,
        parse_json: JSONParser[ResultT],
    ) -> ResultT:
        """Read and parse a single JSON file."""
        ...

    async def read_json_dir(
        self,
        path: PurePath,
        parse_json: JSONParser[ResultT],
        ignore_errors: bool,
    ) -> List[DirectoryEntry[ResultT]]:
        """Read and parse all JSON files in a directory concurrently."""
        ...
