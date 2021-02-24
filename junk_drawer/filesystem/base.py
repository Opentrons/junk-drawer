"""Base filesystem adapter interfaces."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from json import loads as json_loads, dumps as json_dumps
from pathlib import PurePosixPath
from typing import Any, Callable, Generic, List, TypeVar


ResultT = TypeVar("ResultT")


@dataclass
class DirectoryEntry(Generic[ResultT]):
    """Filename and parsed file contents from a full directory read."""

    path: PurePosixPath
    contents: ResultT


JSONParser = Callable[[str], ResultT]
JSONEncoder = Callable[[ResultT], str]


def default_parse_json(text: str) -> Any:
    """Parse a JSON string using builtin `json` module."""
    return json_loads(text)


def default_encode_json(obj: Any) -> str:
    """Encode a value to a JSON string using builtin `json` module."""
    return json_dumps(obj)


class SyncFilesystemLike(ABC):
    """Abstract synchronous filesystem interface."""

    @abstractmethod
    def ensure_dir(self, path: PurePosixPath) -> PurePosixPath:
        """Ensure a directory at `path` exists, creating it if it doesn't."""
        ...

    @abstractmethod
    def read_dir(self, path: PurePosixPath) -> List[str]:
        """Get the stem names of all JSON files in the directory."""
        ...

    @abstractmethod
    def remove_dir(self, path: PurePosixPath) -> None:
        """Delete a directory and everything in it."""
        ...

    @abstractmethod
    def remove(self, path: PurePosixPath) -> None:
        """Delete the file at {path}.json."""
        ...

    @abstractmethod
    def file_exists(self, path: PurePosixPath) -> bool:
        """Return True if `{path}.json` is a file."""
        ...

    @abstractmethod
    def read_json(
        self,
        path: PurePosixPath,
        parse_json: JSONParser[ResultT],
    ) -> ResultT:
        """Read and parse a single JSON file."""
        ...

    @abstractmethod
    def read_json_dir(
        self,
        path: PurePosixPath,
        parse_json: JSONParser[ResultT],
        ignore_errors: bool,
    ) -> List[DirectoryEntry[ResultT]]:
        """Read and parse all JSON files in a directory serially."""
        ...

    @abstractmethod
    def write_json(
        self,
        path: PurePosixPath,
        contents: ResultT,
        encode_json: JSONEncoder[ResultT],
    ) -> None:
        """Write a dictionary object to a JSON file at {path}.json."""
        ...


class AsyncFilesystemLike(ABC):
    """Abstract asynchronous filesystem interface."""

    @property
    @abstractmethod
    def sync(self) -> SyncFilesystemLike:
        """Get the filesystem's underlying synchronous interface."""
        ...

    @abstractmethod
    async def ensure_dir(self, path: PurePosixPath) -> PurePosixPath:
        """Ensure a directory at `path` exists, creating it if it doesn't."""
        ...

    @abstractmethod
    async def read_dir(self, path: PurePosixPath) -> List[str]:
        """Get the stem names of all JSON files in the directory."""
        ...

    @abstractmethod
    async def remove_dir(self, path: PurePosixPath) -> None:
        """Delete a directory and everything in it."""
        ...

    @abstractmethod
    async def remove(self, path: PurePosixPath) -> None:
        """Delete the file at {path}.json."""
        ...

    @abstractmethod
    async def file_exists(self, path: PurePosixPath) -> bool:
        """Return True if `{path}.json` is a file."""
        ...

    @abstractmethod
    async def read_json(
        self,
        path: PurePosixPath,
        parse_json: JSONParser[ResultT],
    ) -> ResultT:
        """Read and parse a single JSON file."""
        ...

    @abstractmethod
    async def read_json_dir(
        self,
        path: PurePosixPath,
        parse_json: JSONParser[ResultT],
        ignore_errors: bool,
    ) -> List[DirectoryEntry[ResultT]]:
        """Read and parse all JSON files in a directory concurrently."""
        ...

    @abstractmethod
    async def write_json(
        self,
        path: PurePosixPath,
        contents: ResultT,
        encode_json: JSONEncoder[ResultT],
    ) -> None:
        """Write a dictionary object to a JSON file at {path}.json."""
        ...
