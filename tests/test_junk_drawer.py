"""Entrypoint tests for junk_drawer."""
from junk_drawer import __version__


def test_version():
    """The version string should be available."""
    assert __version__ == "0.1.0"
