"""Filesystem adapters for junk_drawer."""
from .async_filesystem import AsyncFilesystem
from .sync_filesystem import SyncFilesystem
from .base import AsyncFilesystemLike, DirectoryEntry

from .errors import (
    FileError,
    FileEncodeError,
    FileParseError,
    FileReadError,
    FileWriteError,
    PathNotFoundError,
    RemoveFileError,
)


__all__ = [
    "AsyncFilesystem",
    "AsyncFilesystemLike",
    "DirectoryEntry",
    "FileError",
    "FileEncodeError",
    "FileParseError",
    "FileReadError",
    "FileWriteError",
    "PathNotFoundError",
    "RemoveFileError",
    "SyncFilesystem",
]
