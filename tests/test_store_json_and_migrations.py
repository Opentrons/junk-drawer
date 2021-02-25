"""Tests for the store's JSON and migration handling."""
import pytest
from mock import AsyncMock  # type: ignore[attr-defined]
from pathlib import PurePosixPath
from pydantic import BaseModel
from typing import Any, Dict

from junk_drawer import Store
from .helpers import CoolModel


class StrictModel(CoolModel, BaseModel):
    """Pydantic model that disallows extra fields."""

    class Config:
        """Model config to disallow extra fields."""

        extra = "forbid"


@pytest.fixture
def strict_store(
    store_path: PurePosixPath, mock_filesystem: AsyncMock
) -> Store[StrictModel]:
    """Create a Store with a strict model."""
    return Store(
        directory=store_path,
        schema=StrictModel,
        primary_key=None,
        migrations=(),
        ignore_errors=False,
        filesystem=mock_filesystem,
    )


@pytest.fixture
def migrations_store(
    store_path: PurePosixPath, mock_filesystem: AsyncMock
) -> Store[CoolModel]:
    """Create a Store with migrations."""

    def migration_0(obj: Dict[str, Any]) -> Dict[str, Any]:
        """Add "foo" key."""
        obj["foo"] = "hello"
        return obj

    def migration_1(obj: Dict[str, Any]) -> Dict[str, Any]:
        """Add "bar" key."""
        obj["bar"] = 0
        return obj

    return Store(
        directory=store_path,
        schema=CoolModel,
        primary_key=None,
        migrations=(migration_0, migration_1),
        ignore_errors=False,
        filesystem=mock_filesystem,
    )


def test_encode_json(store: Store[CoolModel]) -> None:
    """It should encode a Pydantic model to a JSON string."""
    model = CoolModel(foo="hello", bar=42)
    result = store.encode_json(model)

    assert result == '{"foo": "hello", "bar": 42, "__schema_version__": 0}'


def test_encode_json_with_migrations(migrations_store: Store[CoolModel]) -> None:
    """It should write the schema version based on migrations."""
    model = CoolModel(foo="hello", bar=42)
    result = migrations_store.encode_json(model)

    assert result == '{"foo": "hello", "bar": 42, "__schema_version__": 2}'


def test_parse_json(store: Store[CoolModel]) -> None:
    """It should parse a JSON string into a Pydantic model."""
    data = '{"foo": "hello", "bar": 42, "__schema_version__": 0}'
    result = store.parse_json(data)

    assert result == CoolModel(foo="hello", bar=42)


def test_parse_json_strict(strict_store: Store[StrictModel]) -> None:
    """It should parse a JSON string into a model with extra: forbid."""
    data = '{"foo": "hello", "bar": 42, "__schema_version__": 0}'
    result = strict_store.parse_json(data)

    assert result == StrictModel(foo="hello", bar=42)


@pytest.mark.parametrize(
    "data,expected",
    [
        ("{}", CoolModel(foo="hello", bar=0)),
        ('{"__schema_version__": 0}', CoolModel(foo="hello", bar=0)),
        ('{"__schema_version__": 1, "foo": "hey"}', CoolModel(foo="hey", bar=0)),
        (
            '{"__schema_version__": 2, "foo": "hey", "bar": 1}',
            CoolModel(foo="hey", bar=1),
        ),
        (
            '{"__schema_version__": 3, "foo": "hey", "bar": 1, "future": "value"}',
            CoolModel(foo="hey", bar=1),
        ),
    ],
)
def test_parse_json_with_migrations(
    migrations_store: Store[CoolModel], data: str, expected: CoolModel
) -> None:
    """It should parse a JSON string and apply migrations from v0."""
    result = migrations_store.parse_json(data)

    assert result == expected
