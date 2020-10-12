"""Filesystem module errors."""

from typing import Union


class PathNotFoundError(ValueError):
    """An error raised when the specified path does not exist."""


class FileReadError(RuntimeError):
    """An error raised when a file is unable to be read."""


class FileParseError(TypeError):
    """An error raised if the file's contents are unable to be parsed."""


FileError = Union[PathNotFoundError, FileReadError, FileParseError]
