"""Base filesystem adapter interfaces."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from json import loads as json_loads, dumps as json_dumps
from pathlib import PurePath
from typing import Any, Callable, Generic, List, TypeVar


ResultT = TypeVar("ResultT")


@dataclass
class DirectoryEntry(Generic[ResultT]):
    """Filename and parsed file contents from a full directory read."""

    path: PurePath
    contents: ResultT


JSONParser = Callable[[str], ResultT]
JSONEncoder = Callable[[ResultT], str]


def default_parse_json(text: str) -> Any:
    """Parse a JSON string using builtin `json` module."""
    return json_loads(text)


def default_encode_json(obj: Any) -> str:
    """Encode a value to a JSON string using builtin `json` module."""
    return json_dumps(obj)


class AsyncFilesystemLike(ABC):
    """Abstract asynchronous filesystem interface."""

    @abstractmethod
    async def ensure_dir(self, path: PurePath) -> PurePath:
        """Ensure a directory at `path` exists, creating it if it doesn't."""
        ...

    @abstractmethod
    async def read_dir(self, path: PurePath) -> List[str]:
        """Get the stem names of all JSON files in the directory."""
        ...

    @abstractmethod
    async def remove_dir(self, path: PurePath) -> None:
        """Delete a directory and everything in it."""
        ...

    @abstractmethod
    async def remove(self, path: PurePath) -> None:
        """Delete the file at {path}.json."""
        ...

    @abstractmethod
    async def file_exists(self, path: PurePath) -> bool:
        """Return True if `{path}.json` is a file."""
        ...

    @abstractmethod
    async def read_json(
        self,
        path: PurePath,
        parse_json: JSONParser[ResultT],
    ) -> ResultT:
        """Read and parse a single JSON file."""
        ...

    @abstractmethod
    async def read_json_dir(
        self,
        path: PurePath,
        parse_json: JSONParser[ResultT],
        ignore_errors: bool,
    ) -> List[DirectoryEntry[ResultT]]:
        """Read and parse all JSON files in a directory concurrently."""
        ...

    @abstractmethod
    async def write_json(
        self,
        path: PurePath,
        contents: ResultT,
        encode_json: JSONEncoder[ResultT],
    ) -> None:
        """Write a dictionary object to a JSON file at {path}.json."""
        ...
