"""junk_drawer error classes."""


class ItemDecodeError(TypeError):
    """
    Exception thrown when the backing data of an item is invalid.

    If this exception is raised, it most likely means that something or someone has
    editted the item's backing JSON file outside of junk_drawer, and those changes
    have caused the item to fail validation.

    Invalid item data can also be the result of an improperly defined migration.
    """


class ItemEncodeError(TypeError):
    """
    Exception thrown when an item was to be encoded into JSON.

    If this exception is raised, the model was unable to be serialized to JSON.
    This probably means the model uses value(s) that are not JSON serializable.
    """


class ItemAccessError(RuntimeError):
    """
    Exception thrown when an item was unable to be accessed.

    If this exception is raised, it means the OS raised some sort of error
    while trying to read from, write to, or delete the backing JSON file.
    """
