"""
Annotate execute_query to accept only safe SQL and parameters as strings.
"""

from typing import Iterable, LiteralString


def execute_query(sql: LiteralString, parameters: Iterable[str] = ...) -> None:
    ...
