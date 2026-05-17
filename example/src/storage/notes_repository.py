"""Репозиторий заметок поверх JSON-хранилища."""

from __future__ import annotations

import os

from ..domain.note import Note
from ..storage.json_store import JsonStore


class NotesRepository:
    """CRUD заметок с персистентностью в ``<base_dir>/notes.json``.

    :param base_dir: каталог данных плагина.
    """

    def __init__(self, base_dir: str) -> None:
        self._store = JsonStore(os.path.join(base_dir, "notes.json"))

    def _read(self) -> list[Note]:
        raw = self._store.load(default=[])
        notes = []
        for item in raw if isinstance(raw, list) else []:
            try:
                notes.append(Note.from_dict(item))
            except (KeyError, ValueError, TypeError):
                continue
        return notes

    def _write(self, notes: list[Note]) -> None:
        self._store.save([note.to_dict() for note in notes])

    def list(self) -> list[Note]:
        """Вернуть все заметки в порядке добавления."""
        return self._read()

    def add(self, text: str, created: str) -> Note:
        """Добавить заметку и вернуть её."""
        notes = self._read()
        next_id = (max((n.id for n in notes), default=0)) + 1
        note = Note(id=next_id, text=text, created=created)
        notes.append(note)
        self._write(notes)
        return note

    def delete(self, note_id: int) -> bool:
        """Удалить заметку по идентификатору. ``True`` если удалена."""
        notes = self._read()
        remaining = [n for n in notes if n.id != note_id]
        if len(remaining) == len(notes):
            return False
        self._write(remaining)
        return True

    def clear(self) -> int:
        """Удалить все заметки, вернуть число удалённых."""
        count = len(self._read())
        self._write([])
        return count
