"""Test helper classes."""
from pydantic import BaseModel
from typing import Union


class CoolModel(BaseModel):
    """Simple Pydantic model for to act as the Store's schema."""

    foo: Union[int, str]
    bar: int
