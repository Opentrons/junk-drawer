"""Store module for junk_drawer."""
from __future__ import annotations
from logging import getLogger
from pathlib import PurePath
from pydantic import BaseModel
from typing import (
    Callable,
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

ModelT = TypeVar("ModelT", bound=BaseModel)

Migration = Callable[[dict], dict]

log = getLogger(__name__)


class Store(Generic[ModelT]):
    """A Store class is used to create and manage a collection of items."""

    @classmethod
    async def create(
        cls: Type[Store[ModelT]],
        directory: Union[str, PurePath],
        schema: Type[ModelT],
        *,
        primary_key: Optional[str] = None,
        migrations: Sequence[Migration] = (),
        ignore_errors: bool = False,
    ) -> Store[ModelT]:
        """Create a Store, waiting for the directory to be set up if necessary."""
        directory = PurePath(directory)
        filesystem = AsyncFilesystem()

        await filesystem.ensure_dir(directory)

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
        key_path = self._directory / key
        return await self._filesystem.file_exists(key_path)

    async def get(self, key: str) -> Optional[ModelT]:
        """Get an item from the store by key, if that key exists."""
        key_path = self._directory / key
        read_result = None
        try:
            read_result = await self._filesystem.read_json(
                key_path, parse_json=self.parse_json
            )
        except (PathNotFoundError, FileParseError, FileReadError) as error:
            self._maybe_raise_file_error(error)

        return read_result

    async def get_all_keys(self) -> List[str]:
        """Get all keys in the store."""
        return await self._filesystem.read_dir(self._directory)

    async def get_all_entries(self) -> List[Tuple[str, ModelT]]:
        """Get all keys in the store."""
        try:
            dir_entries = await self._filesystem.read_json_dir(
                self._directory,
                parse_json=self.parse_json,
                ignore_errors=self._ignore_errors,
            )
        except (PathNotFoundError, FileParseError, FileReadError) as error:
            self._maybe_raise_file_error(error)

        return [(entry.path.stem, entry.contents) for entry in dir_entries]

    async def get_all_items(self) -> List[ModelT]:
        """Get all keys in the store."""
        entries = await self.get_all_entries()
        return [item for key, item in entries]

    async def put(self, item: ModelT, key: Optional[str] = None) -> Optional[str]:
        """
        Put a single item to the store at key.

        Returns the key of the added item. If `ignore_errors` is set to `True`,
        `put` will return None if the item was unable to be added.
        """
        item_key = self._get_item_key(item, key)
        key_path = self._directory / item_key
        put_key = None

        try:
            await self._filesystem.write_json(
                key_path, item, encode_json=self.encode_json
            )
            put_key = item_key
        except (FileWriteError, FileEncodeError) as error:
            self._maybe_raise_file_error(error)

        return put_key

    async def ensure(self, default_item: ModelT, key: Optional[str] = None) -> ModelT:
        """
        Ensure an item exists in the store at the given key.

        If an item with `key` already exists, `ensure` will return the item. If
        no item with `key` exists, it will write `default_item` to the store
        before returning the item.

        This method is a shortcut for a `get` followed by a `put` if the `get`
        returns `None`.
        """
        item_key = self._get_item_key(default_item, key)
        result = await self.get(item_key)

        if result is None:
            await self.put(default_item, key)
            result = default_item

        return result

    async def delete(self, key: str) -> Optional[str]:
        """
        Delete a single item in the store.

        Returns the deleted key if the item was removed or None if no item was
        found at that key. If `ignore_errors` is set, delete will also return
        None if the item is unable to be removed.
        """
        key_path = self._directory / key
        removed_key = None

        try:
            await self._filesystem.remove(key_path)
            removed_key = key
        except (PathNotFoundError, RemoveFileError) as error:
            self._maybe_raise_file_error(error)

        return removed_key

    async def delete_store(self) -> None:
        """Delete the store and all its items."""
        return await self._filesystem.remove_dir(self._directory)

    def encode_json(self, item: ModelT) -> str:
        """Encode a model instance into JSON."""
        obj = item.dict()
        obj[SCHEMA_VERSION_KEY] = len(self._migrations)

        # NOTE(mc, 2020-10-25): __json_encoder__ is an undocumented property
        # of BaseModel, but its usage here is to ensure Pydantic model config
        # related to serialization is properly used. This functionality is
        # covered by basic integration tests
        return item.__config__.json_dumps(obj, default=item.__json_encoder__)

    def parse_json(self, data: str) -> ModelT:
        """Decode a string into a model instance."""
        obj = self._schema.__config__.json_loads(data)
        schema_version = obj.pop(SCHEMA_VERSION_KEY, 0)

        for migrate in self._migrations[schema_version:]:
            obj = migrate(obj)

        return self._schema.parse_obj(obj)

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
