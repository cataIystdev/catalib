"""Команда ``.note`` — управление заметками (add/list/del/clear)."""

from __future__ import annotations

from ...core.command import Command
from ...core.errors import CommandError
from ...services.notes_service import NotesService


class NoteCommand(Command):
    """``.note add <текст>`` | ``list`` | ``del <id>`` | ``clear``."""

    name = "note"
    summary = "заметки: add <текст> | list | del <id> | clear"
    usage = "add|list|del|clear [аргумент]"

    def __init__(self, service: NotesService) -> None:
        self._service = service

    def execute(self, args: str) -> str:
        parts = args.split(maxsplit=1)
        if not parts:
            raise CommandError("подкоманда: add | list | del | clear")
        sub = parts[0].lower()
        rest = parts[1] if len(parts) > 1 else ""
        if sub == "add":
            return self._service.add(rest)
        if sub == "list":
            return self._service.list()
        if sub == "del":
            return self._service.delete(rest)
        if sub == "clear":
            return self._service.clear()
        raise CommandError("подкоманда: add | list | del | clear")
