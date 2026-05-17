"""Доменная модель заметки."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Note:
    """Заметка пользователя.

    :param id: порядковый идентификатор (уникален в пределах хранилища).
    :param text: текст заметки.
    :param created: время создания в ISO 8601.
    """

    id: int
    text: str
    created: str

    def to_dict(self) -> dict:
        """Сериализовать в словарь для JSON-хранилища."""
        return {"id": self.id, "text": self.text, "created": self.created}

    @staticmethod
    def from_dict(data: dict) -> Note:
        """Восстановить из словаря JSON-хранилища."""
        return Note(id=int(data["id"]), text=str(data["text"]), created=str(data["created"]))
