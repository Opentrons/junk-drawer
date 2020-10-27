"""Entrypoint and end-to-end tests for junk_drawer."""
import pytest
from pathlib import PurePath
from pydantic import BaseModel
from junk_drawer import Store
from typing import Optional

pytestmark = pytest.mark.asyncio


class CoolModel(BaseModel):
    """A model to test with."""

    foo: str
    bar: str
    baz: Optional[int] = None


class OldModel(BaseModel):
    """A model at an "older" schema version."""

    foo: str


async def test_store_write_and_read(real_store_path: PurePath) -> None:
    """A store should be able to write and read a file."""
    store = await Store.create(real_store_path, schema=CoolModel)
    item = CoolModel(foo="hello", bar="world")

    key = await store.put(item, "foo")

    assert key == "foo"

    result = await store.get(key)

    assert result == CoolModel(foo="hello", bar="world")


async def test_store_write_and_read_dir(real_store_path: PurePath) -> None:
    """A store should be able to write and read the whole store."""
    store = await Store.create(real_store_path, schema=CoolModel)

    # TODO(mc, 2020-10-03): replace with store.add
    await store.put(CoolModel(foo="hello", bar="world"), "foo")
    await store.put(CoolModel(foo="oh", bar="hai"), "bar")

    result = await store.get_all_entries()

    assert len(result) == 2
    assert ("foo", CoolModel(foo="hello", bar="world")) in result
    assert ("bar", CoolModel(foo="oh", bar="hai")) in result


async def test_store_write_and_ensure(real_store_path: PurePath) -> None:
    """A store should be able to write and read a file."""
    store = await Store.create(real_store_path, schema=CoolModel)
    default_item = CoolModel(foo="default", bar="value")
    item = CoolModel(foo="hello", bar="world")

    result = await store.ensure(default_item, "foo")
    assert result == default_item

    await store.put(item, "foo")
    result = await store.ensure(default_item, "foo")

    assert result == item


async def test_keyed_store_write_and_read(real_store_path: PurePath) -> None:
    """A store should be able to write and read a file."""
    store = await Store.create(real_store_path, schema=CoolModel, primary_key="foo")
    item = CoolModel(foo="hello", bar="world")

    key = await store.put(item)

    assert key == "hello"

    result = await store.get(key)

    assert result == CoolModel(foo="hello", bar="world")


async def test_keyed_store_write_and_read_dir(real_store_path: PurePath) -> None:
    """A store should be able to write and read the whole store."""
    store = await Store.create(real_store_path, schema=CoolModel, primary_key="foo")

    # TODO(mc, 2020-10-03): replace with store.add
    await store.put(CoolModel(foo="hello", bar="world"))
    await store.put(CoolModel(foo="oh", bar="hai"))

    result = await store.get_all_entries()

    assert len(result) == 2
    assert ("hello", CoolModel(foo="hello", bar="world")) in result
    assert ("oh", CoolModel(foo="oh", bar="hai")) in result


async def test_keyed_store_write_and_ensure(real_store_path: PurePath) -> None:
    """A store should be able to write and read a file."""
    store = await Store.create(real_store_path, schema=CoolModel, primary_key="foo")
    default_item = CoolModel(foo="some-key", bar="hello world")
    item = CoolModel(foo="some-key", bar="oh hai")

    result = await store.ensure(default_item)
    assert result == default_item

    await store.put(item)
    result = await store.ensure(default_item)

    assert result == item


async def test_store_write_and_read_with_migrations(real_store_path: PurePath) -> None:
    """A store should be able to write and read a file."""
    old_store = await Store.create(real_store_path, schema=OldModel)

    item_key = "some-key"
    item = OldModel(foo="hello")

    await old_store.put(item, item_key)

    new_store = await Store.create(
        real_store_path,
        schema=CoolModel,
        migrations=(
            lambda obj: {"foo": obj["foo"], "bar": "world"},
            lambda obj: {"foo": obj["foo"], "bar": obj["bar"], "baz": 0},
        ),
    )

    result = await new_store.get(item_key)

    assert result == CoolModel(foo="hello", bar="world", baz=0)
