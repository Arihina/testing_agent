"""Модели данных."""

from pydantic import BaseModel


class User(BaseModel):
    id: int
    name: str
    email: str


def age_group(age: int) -> str:
    """Возвращает возрастную группу."""
    if age < 18:
        return "child"
    if age < 65:
        return "adult"
    return "senior"
