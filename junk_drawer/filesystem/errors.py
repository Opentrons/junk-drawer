"""Filesystem module errors."""

from typing import Union


class PathNotFoundError(ValueError):
    """An error raised when the specified path does not exist."""


class RemoveFileError(RuntimeError):
    """An error raised when a file is unable to be removed."""


class FileReadError(RuntimeError):
    """An error raised when a file is unable to be read."""


class FileWriteError(RuntimeError):
    """An error raised when a file is unable to be written."""


class FileRemoveError(RuntimeError):
    """An error raised when a file is unable to be removed."""


class FileParseError(TypeError):
    """An error raised if the file's contents are unable to be parsed."""


class FileEncodeError(TypeError):
    """An error raised if the file's contents are unable to be encoded."""


FileError = Union[
    PathNotFoundError,
    FileEncodeError,
    FileReadError,
    FileWriteError,
    FileParseError,
    RemoveFileError,
]
