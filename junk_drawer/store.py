"""Store module for junk_drawer."""
from __future__ import annotations
from logging import getLogger
from pathlib import PurePath
from pydantic import BaseModel
from typing import Generic, List, Optional, Tuple, TypeVar, Type, Union
from .filesystem import (
    AsyncFilesystemLike,
    AsyncFilesystem,
    PathNotFoundError,
    FileReadError,
    FileParseError,
    FileError,
)
from .errors import InvalidItemDataError, ItemAccessError

M = TypeVar("M", bound=BaseModel)

log = getLogger(__name__)


class Store(Generic[M]):
    """A Store class is used to create and manage a collection of items."""

    @classmethod
    async def create(
        cls: Type[Store[M]],
        directory: Union[str, PurePath],
        schema: Type[M],
        filesystem: Optional[AsyncFilesystemLike] = None,
        ignore_errors: bool = False,
    ) -> Store[M]:
        """Create a Store, waiting for the directory to be set up if necessary."""
        directory = PurePath(directory)
        filesystem = filesystem if filesystem is not None else AsyncFilesystem()

        await filesystem.ensure_dir(directory)

        return cls(
            directory=directory,
            schema=schema,
            filesystem=filesystem,
            ignore_errors=ignore_errors,
        )

    def __init__(
        self,
        directory: PurePath,
        schema: Type[M],
        filesystem: AsyncFilesystemLike,
        ignore_errors: bool,
    ) -> None:
        """Initialize a Store; use Store.create instead."""
        self._schema = schema
        self._directory = directory
        self._filesystem = filesystem
        self._ignore_errors = ignore_errors

    async def exists(self, key: str) -> bool:
        """Check whether a key exists in the store."""
        key_path = self._directory / key
        return await self._filesystem.file_exists(key_path)

    async def get(self, key: str) -> Optional[M]:
        """Get an item from the store by key, if that key exists."""
        key_path = self._directory / key
        read_result = None
        try:
            read_result = await self._filesystem.read_json(
                key_path, parse_json=self._schema.parse_raw
            )
        except (PathNotFoundError, FileParseError, FileReadError) as error:
            self._maybe_raise_read_error(error)

        return read_result

    async def get_all_keys(self) -> List[str]:
        """Get all keys in the store."""
        basenames = await self._filesystem.read_dir(self._directory)
        return basenames

    async def get_all_entries(self) -> List[Tuple[str, M]]:
        """Get all keys in the store."""
        try:
            dir_entries = await self._filesystem.read_json_dir(
                self._directory,
                parse_json=self._schema.parse_raw,
                ignore_errors=self._ignore_errors,
            )
        except (PathNotFoundError, FileParseError, FileReadError) as error:
            self._maybe_raise_read_error(error)

        return [(entry.path.stem, entry.contents) for entry in dir_entries]

    async def get_all_items(self) -> List[M]:
        """Get all keys in the store."""
        entries = await self.get_all_entries()
        return [item for key, item in entries]

    def _maybe_raise_read_error(self, error: FileError) -> None:
        if not self._ignore_errors:
            if isinstance(error, FileParseError):
                raise InvalidItemDataError(str(error))
            elif isinstance(error, FileReadError):
                raise ItemAccessError(str(error))
