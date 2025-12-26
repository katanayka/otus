"""
Define a callable type that accepts a string argument and returns None.
"""

from collections.abc import Callable

SingleStringInput = Callable[[str], None]
