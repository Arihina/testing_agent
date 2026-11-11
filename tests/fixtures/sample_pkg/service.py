"""Сервисный слой: класс с методами и вызовом функций модуля."""

from .models import User
from .utils import normalize


def _sort_by_id(users: list[User]) -> list[User]:
    """Сортирует пользователей по id."""
    return sorted(users, key=lambda u: u.id)


class UserService:
    def __init__(self, users: list[User] | None = None):
        self._users = users or []

    def add_user(self, user: User) -> User:
        """Добавляет пользователя."""
        self._users.append(user)
        return user

    def find_by_name(self, name: str) -> list[User]:
        """Находит пользователей по имени."""
        result = []
        for u in self._users:
            if u.name == name:
                result.append(u)
        return result

    def names(self) -> list[str]:
        return normalize([u.name for u in self._users])

    def get_or_create(self, email: str) -> User:
        """Возвращает пользователя по email или создаёт нового."""
        for u in self._users:
            if u.email == email:
                return u
        user = User(id=len(self._users) + 1, name=email.split("@")[0], email=email)
        self._users.append(user)
        return user

    def sorted_users(self) -> list[User]:
        """Возвращает пользователей, отсортированных по id."""
        return _sort_by_id(self._users)

    def _reindex(self) -> None:
        self._users.sort(key=lambda u: u.id)


def rank_users(users: list[User]) -> dict[str, int]:
    """Ранжирует пользователей по длине имени."""
    ranks = {}
    for i, u in enumerate(users):
        if len(u.name) > 5:
            rank = 2
        elif len(u.name) > 2:
            rank = 3
        else:
            rank = 1
        ranks[u.name] = rank + i
    return ranks
