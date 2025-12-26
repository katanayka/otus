"""
Define a class `Student` that represents a dictionary with keys:
name (str), age (int), school (str).
"""

from typing import TypedDict


class Student(TypedDict):
    name: str
    age: int
    school: str
