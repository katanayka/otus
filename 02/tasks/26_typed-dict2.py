"""
Define a class `Student` that represents a dictionary with keys:
name (str), age (int), school (str, optional).
"""

from typing import NotRequired, TypedDict


class Student(TypedDict):
    name: str
    age: int
    school: NotRequired[str]
