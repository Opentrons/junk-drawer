"""Store module for junk_drawer."""
from __future__ import annotations
from logging import getLogger
from typing import Optional

from .read_store import SCHEMA_VERSION_KEY, ReadStore, ModelT

from .filesystem import (
    PathNotFoundError,
    RemoveFileError,
    FileEncodeError,
    FileWriteError,
)

log = getLogger(__name__)


class Store(ReadStore[ModelT]):
    """A Store class is used to create and manage a collection of items."""

    async def put(self, item: ModelT, key: Optional[str] = None) -> Optional[str]:
        """
        Put a single item to the store.

        Returns the key of the added item. If `ignore_errors` is set to `True`,
        `put` will return None if the item was unable to be added.
        """
        item_key = self._get_item_key(item, key)
        key_path = self._get_key_path(item_key)

        try:
            await self._filesystem.write_json(
                key_path, item, encode_json=self.encode_json
            )
            return item_key
        except (FileWriteError, FileEncodeError) as error:
            self._maybe_raise_file_error(error)
            return None

    def put_sync(self, item: ModelT, key: Optional[str] = None) -> Optional[str]:
        """
        Put a single item to the store.

        Synchronous version of :py:meth:`put`.
        """
        item_key = self._get_item_key(item, key)
        key_path = self._get_key_path(item_key)

        try:
            self._filesystem.sync.write_json(
                key_path, item, encode_json=self.encode_json
            )
            return item_key
        except (FileWriteError, FileEncodeError) as error:
            self._maybe_raise_file_error(error)
            return None

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

    def ensure_sync(self, default_item: ModelT, key: Optional[str] = None) -> ModelT:
        """
        Ensure an item exists in the store at the given key.

        Synchronous version of :py:meth:`ensure`.
        """
        item_key = self._get_item_key(default_item, key)
        result = self.get_sync(item_key)

        if result is None:
            self.put_sync(default_item, key)
            result = default_item

        return result

    async def delete(self, key: str) -> Optional[str]:
        """
        Delete a single item in the store.

        Returns the deleted key if the item was removed or None if no item was
        found at that key. If `ignore_errors` is set, delete will also return
        None if the item is unable to be removed.
        """
        key_path = self._get_key_path(key)

        try:
            await self._filesystem.remove(key_path)
            return key
        except (PathNotFoundError, RemoveFileError) as error:
            self._maybe_raise_file_error(error)
            return None

    def delete_sync(self, key: str) -> Optional[str]:
        """
        Delete a single item in the store.

        Synchronous version of :py:meth:`delete`.
        """
        key_path = self._get_key_path(key)

        try:
            self._filesystem.sync.remove(key_path)
            return key
        except (PathNotFoundError, RemoveFileError) as error:
            self._maybe_raise_file_error(error)
            return None

    async def delete_store(self) -> None:
        """Delete the store and all its items."""
        return await self._filesystem.remove_dir(self._directory)

    def delete_store_sync(self) -> None:
        """
        Delete the store and all its items.

        Synchronous version of :py:meth:`delete_store`.
        """
        return self._filesystem.sync.remove_dir(self._directory)

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
