"""Бизнес-логика заметок: валидация ввода и форматирование вывода."""

from __future__ import annotations

from datetime import datetime

from ..core.errors import CommandError
from ..storage.notes_repository import NotesRepository
from ..util.textwrap_helpers import shorten

#: Предел длины текста заметки.
_MAX_NOTE_LEN = 2000


class NotesService:
    """Операции над заметками с человекочитаемыми ответами.

    :param repository: репозиторий заметок.
    :param clock: функция текущего времени (для тестируемости).
    """

    def __init__(self, repository: NotesRepository, clock=datetime.now) -> None:
        self._repo = repository
        self._clock = clock

    def add(self, text: str) -> str:
        """Добавить заметку."""
        text = text.strip()
        if not text:
            raise CommandError("текст заметки пуст")
        if len(text) > _MAX_NOTE_LEN:
            raise CommandError(f"заметка длиннее {_MAX_NOTE_LEN} символов")
        note = self._repo.add(text, self._clock().isoformat(timespec="seconds"))
        return f"заметка #{note.id} сохранена"

    def list(self) -> str:
        """Вернуть нумерованный список заметок."""
        notes = self._repo.list()
        if not notes:
            return "заметок нет"
        lines = ["Заметки:"]
        lines += [f"#{n.id} [{n.created}] {shorten(n.text, 120)}" for n in notes]
        return "\n".join(lines)

    def delete(self, raw_id: str) -> str:
        """Удалить заметку по идентификатору."""
        try:
            note_id = int(raw_id.strip())
        except ValueError as exc:
            raise CommandError("ожидается числовой идентификатор") from exc
        if self._repo.delete(note_id):
            return f"заметка #{note_id} удалена"
        raise CommandError(f"заметка #{note_id} не найдена")

    def clear(self) -> str:
        """Удалить все заметки."""
        return f"удалено заметок: {self._repo.clear()}"
