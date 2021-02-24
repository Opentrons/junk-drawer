"""Read-only store module for junk_drawer."""
from __future__ import annotations
from logging import getLogger
from pathlib import PurePath, PurePosixPath
from pydantic import BaseModel
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
    Type,
    Union,
)

from .errors import ItemDecodeError, ItemEncodeError, ItemAccessError

from .filesystem import (
    AsyncFilesystemLike,
    AsyncFilesystem,
    PathNotFoundError,
    RemoveFileError,
    FileEncodeError,
    FileReadError,
    FileParseError,
    FileWriteError,
    FileError,
)


SCHEMA_VERSION_KEY = "__schema_version__"

StoreT = TypeVar("StoreT", bound="ReadStore")
ModelT = TypeVar("ModelT", bound=BaseModel)

Migration = Callable[[Dict[str, Any]], Dict[str, Any]]

log = getLogger(__name__)


class ReadStore(Generic[ModelT]):
    """A Store class is used to manage reading a collection of items."""

    @classmethod
    def create(
        cls: Type[StoreT],
        directory: Union[str, PurePath],
        schema: Type[ModelT],
        *,
        primary_key: Optional[str] = None,
        migrations: Sequence[Migration] = (),
        ignore_errors: bool = False,
    ) -> StoreT:
        """Create a new ReadStore."""
        directory = PurePath(directory)
        filesystem = AsyncFilesystem.create()

        return cls(
            directory=directory,
            schema=schema,
            migrations=migrations,
            primary_key=primary_key,
            ignore_errors=ignore_errors,
            filesystem=filesystem,
        )

    def __init__(
        self,
        directory: PurePath,
        schema: Type[ModelT],
        *,
        primary_key: Optional[str],
        migrations: Sequence[Migration],
        ignore_errors: bool,
        filesystem: AsyncFilesystemLike,
    ) -> None:
        """Initialize a Store; use Store.create instead."""
        self._directory = directory
        self._schema = schema
        self._migrations = migrations
        self._primary_key = primary_key
        self._filesystem = filesystem
        self._ignore_errors = ignore_errors

    async def exists(self, key: str) -> bool:
        """Check whether a key exists in the store."""
        key_path = self._get_key_path(key)
        return await self._filesystem.file_exists(key_path)

    def exists_sync(self, key: str) -> bool:
        """
        Check whether a key exists in the store.

        Synchronous version of :py:meth:`exists`.
        """
        key_path = self._get_key_path(key)
        return self._filesystem.sync.file_exists(key_path)

    async def get(self, key: str) -> Optional[ModelT]:
        """Get an item from the store by key, if that key exists."""
        key_path = self._get_key_path(key)

        try:
            return await self._filesystem.read_json(
                key_path, parse_json=self.parse_json
            )
        except (PathNotFoundError, FileParseError, FileReadError) as error:
            self._maybe_raise_file_error(error)
            return None

    def get_sync(self, key: str) -> Optional[ModelT]:
        """
        Get an item from the store by key, if that key exists.

        Synchronous version of :py:meth:`get`.
        """
        key_path = self._get_key_path(key)

        try:
            return self._filesystem.sync.read_json(key_path, parse_json=self.parse_json)
        except (PathNotFoundError, FileParseError, FileReadError) as error:
            self._maybe_raise_file_error(error)
            return None

    async def get_all_keys(self) -> List[str]:
        """Get all keys in the store."""
        return await self._filesystem.read_dir(self._directory)

    def get_all_keys_sync(self) -> List[str]:
        """
        Get all keys in the store.

        Synchronous version of :py:meth:`get_all_keys`.
        """
        return self._filesystem.sync.read_dir(self._directory)

    async def get_all_entries(self) -> List[Tuple[str, ModelT]]:
        """Get all key, item entry pairs in the store."""
        try:
            dir_entries = await self._filesystem.read_json_dir(
                self._directory,
                parse_json=self.parse_json,
                ignore_errors=self._ignore_errors,
            )
        except (PathNotFoundError, FileParseError, FileReadError) as error:
            self._maybe_raise_file_error(error)

        return [(entry.path.stem, entry.contents) for entry in dir_entries]

    def get_all_entries_sync(self) -> List[Tuple[str, ModelT]]:
        """
        Get all key, item entry pairs in the store.

        Synchronous version of :py:meth:`get_all_entries`.
        """
        try:
            dir_entries = self._filesystem.sync.read_json_dir(
                self._directory,
                parse_json=self.parse_json,
                ignore_errors=self._ignore_errors,
            )
        except (PathNotFoundError, FileParseError, FileReadError) as error:
            self._maybe_raise_file_error(error)

        return [(entry.path.stem, entry.contents) for entry in dir_entries]

    async def get_all_items(self) -> List[ModelT]:
        """Get all items in the store."""
        entries = await self.get_all_entries()
        return [item for key, item in entries]

    def get_all_items_sync(self) -> List[ModelT]:
        """
        Get all items in the store.

        Synchronous version of :py:meth:`get_all_items`.
        """
        entries = self.get_all_entries_sync()
        return [item for key, item in entries]

    def parse_json(self, data: str) -> ModelT:
        """Decode a string into a model instance."""
        obj = self._schema.__config__.json_loads(data)
        schema_version = obj.pop(SCHEMA_VERSION_KEY, 0)

        for migrate in self._migrations[schema_version:]:
            obj = migrate(obj)

        return self._schema.parse_obj(obj)

    def _get_key_path(self, key: str) -> PurePath:
        return PurePosixPath(self._directory / key)

    def _get_item_key(self, item: ModelT, key: Optional[str]) -> str:
        item_key = (
            getattr(item, self._primary_key, None)
            if self._primary_key is not None
            else key
        )

        assert item_key is not None, "key or a model with a primary_key required"

        return str(item_key)

    def _maybe_raise_file_error(self, error: FileError) -> None:
        if not self._ignore_errors:
            if isinstance(error, FileParseError):
                raise ItemDecodeError(str(error))
            elif isinstance(error, FileEncodeError):
                raise ItemEncodeError(str(error))
            elif isinstance(error, (FileReadError, FileWriteError, RemoveFileError)):
                raise ItemAccessError(str(error))
