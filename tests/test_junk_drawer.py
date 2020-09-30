"""Entrypoint and e2e tests for junk_drawer."""
import pytest
from pydantic import BaseModel
from junk_drawer import Store


pytestmark = pytest.mark.asyncio


class CoolModel(BaseModel):
    """A model to test with."""

    foo: str
    bar: str


async def test_store_write_and_read(tmp_path):
    """A store should be able to write and read a file."""
    store = await Store.create(tmp_path, schema=CoolModel)

    # TODO(mc, 2020-10-03): replace with store.add
    (tmp_path / "foo.json").write_text(CoolModel(foo="hello", bar="world").json())
    result = await store.get("foo")

    assert result == CoolModel(foo="hello", bar="world")


async def test_store_write_and_read_dir(tmp_path):
    """A store should be able to write and read the whole store."""
    store = await Store.create(tmp_path, schema=CoolModel)

    # TODO(mc, 2020-10-03): replace with store.add
    (tmp_path / "foo.json").write_text(CoolModel(foo="hello", bar="world").json())
    (tmp_path / "bar.json").write_text(CoolModel(foo="oh", bar="hai").json())

    result = await store.get_all_entries()

    assert result == [
        ("foo", CoolModel(foo="hello", bar="world")),
        ("bar", CoolModel(foo="oh", bar="hai")),
    ]
