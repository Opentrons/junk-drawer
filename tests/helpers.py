"""Test helper classes."""
from pathlib import PurePath
from pydantic import BaseModel
from typing import Union


class CoolModel(BaseModel):
    """Simple Pydantic model for to act as the Store's schema."""

    foo: Union[int, str]
    bar: int


STORE_PATH_STR = "./store"

store_path = PurePath(STORE_PATH_STR)
