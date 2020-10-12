"""junk_drawer error classes."""


class InvalidItemDataError(Exception):
    """
    Exception thrown when the backing data of an item is invalid.

    If this exception is raised, it most likely means that something or someone has
    editted the item's backing JSON file outside of junk_drawer, and those changes
    have caused the item to fail validation.

    Invalid item data can also be the result of an improperly defined migration.
    """


class ItemAccessError(Exception):
    """
    Exception thrown when an item was unable to be accessed.

    If this exception is raised, it means the OS raised some sort of error
    while trying to open and read the file.
    """
