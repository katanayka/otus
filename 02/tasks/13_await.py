"""
`run_async` takes an awaitable integer.
"""

from collections.abc import Awaitable


def run_async(func: Awaitable[int]):
    """No implementation needed."""