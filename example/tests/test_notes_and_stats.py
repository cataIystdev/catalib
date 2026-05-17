"""Тесты сервисов заметок и статистики (с временным каталогом)."""

from datetime import datetime
from pathlib import Path

import pytest
from src.core.errors import CommandError
from src.services.notes_service import NotesService
from src.services.stats_service import StatsService
from src.storage.notes_repository import NotesRepository


def _fixed_clock() -> datetime:
    return datetime(2026, 5, 17, 12, 0, 0)


def _service(tmp_path: Path) -> NotesService:
    return NotesService(NotesRepository(str(tmp_path)), clock=_fixed_clock)


def test_notes_add_list_delete_clear(tmp_path: Path) -> None:
    service = _service(tmp_path)
    assert service.list() == "заметок нет"
    assert service.add("первая") == "заметка #1 сохранена"
    assert service.add("вторая") == "заметка #2 сохранена"
    listing = service.list()
    assert "#1" in listing and "#2" in listing and "первая" in listing
    assert service.delete("1") == "заметка #1 удалена"
    with pytest.raises(CommandError, match="не найдена"):
        service.delete("1")
    assert service.clear() == "удалено заметок: 1"
    assert service.list() == "заметок нет"


def test_notes_persist_across_instances(tmp_path: Path) -> None:
    _service(tmp_path).add("сохранится")
    assert "сохранится" in _service(tmp_path).list()


def test_notes_validation(tmp_path: Path) -> None:
    service = _service(tmp_path)
    with pytest.raises(CommandError, match="пуст"):
        service.add("   ")
    with pytest.raises(CommandError, match="идентификатор"):
        service.delete("abc")


def test_stats_counts_and_summary(tmp_path: Path) -> None:
    stats = StatsService(str(tmp_path))
    assert stats.summary() == "статистика пуста"
    stats.increment("calc")
    stats.increment("calc")
    stats.increment("roll")
    summary = stats.summary()
    assert "calc: 2" in summary
    assert summary.index("calc: 2") < summary.index("roll: 1")
