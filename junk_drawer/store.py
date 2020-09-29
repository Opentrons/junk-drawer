"""Store module for junk_drawer."""
from logging import getLogger
from pathlib import PurePath
from pydantic import BaseModel, ValidationError
from typing import Generic, List, Optional, Tuple, TypeVar, Type
from .filesystem import AsyncFilesystemLike
from .errors import InvalidItemDataError

S = TypeVar("S", bound="Store")
M = TypeVar("M", bound=BaseModel)

log = getLogger(__name__)


class Store(Generic[S, M]):
    """A Store class is used to create and manage a collection of items."""

    @classmethod
    async def create(
        cls: Type[S],
        name: str,
        schema: Type[M],
        filesystem: AsyncFilesystemLike,
        raise_on_validation_error: bool = True,
    ) -> S:
        """Create a Store, waiting for the directory to be set up if necessary."""
        directory = PurePath(name)
        await filesystem.ensure_dir(directory)

        return cls(
            directory=directory,
            schema=schema,
            filesystem=filesystem,
            raise_on_validation_error=raise_on_validation_error,
        )

    def __init__(
        self,
        directory: PurePath,
        schema: Type[M],
        filesystem: AsyncFilesystemLike,
        raise_on_validation_error: bool,
    ) -> None:
        """Initialize a Store; use Store.create instead."""
        self._schema = schema
        self._directory = directory
        self._fs = filesystem
        self._raise_on_validation_error = raise_on_validation_error

    async def exists(self, key: str) -> bool:
        """Check whether a key exists in the store."""
        key_path = self._directory / key
        return await self._fs.file_exists(key_path)

    async def get(self, key: str) -> Optional[M]:
        """Get an item from the store by key, if that key exists."""
        key_path = self._directory / key

        try:
            obj = await self._fs.read_json(key_path)
            item = self._parse_obj(obj)
        except FileNotFoundError:
            item = None

        return item

    async def get_all_keys(self) -> List[str]:
        """Get all keys in the store."""
        basenames = await self._fs.read_dir(self._directory)
        return basenames

    async def get_all_entries(self) -> List[Tuple[str, M]]:
        """Get all keys in the store."""
        obj_entries = await self._fs.read_json_dir(self._directory)
        item_entries = [(key, self._parse_obj(obj)) for key, obj in obj_entries]
        return [(key, item) for key, item in item_entries if item is not None]

    async def get_all_items(self) -> List[M]:
        """Get all keys in the store."""
        entries = await self.get_all_entries()
        return [item for key, item in entries]

    def _parse_obj(self, obj: dict) -> Optional[M]:
        item = None

        try:
            item = self._schema.parse_obj(obj)
        except ValidationError as error:
            log.exception("Validation error while parsing object")
            if self._raise_on_validation_error:
                raise InvalidItemDataError(str(error))

        return item
