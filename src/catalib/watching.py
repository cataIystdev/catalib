"""Слежение за файлами с фолбэком на stdlib-поллинг.

``watchfiles`` (Rust-бэкенд) мгновенный и дешёвый по CPU, но не имеет
колёс под Android и сложно собирается на Termux. Поэтому он
**предпочтителен, но не обязателен**: если пакета нет — используется
поллинг по `mtime`/размеру на чистой stdlib. Команда ``watch`` больше не
падает без ``watchfiles`` (ревизия ADR-0005; см. ADR-0011).

Чистая логика снимка/диффа вынесена в :func:`_snapshot`/:func:`_diff` и
тестируется без бесконечного цикла; сам цикл — :func:`iter_changes`.
"""

from __future__ import annotations

import time
from collections.abc import Iterator
from pathlib import Path

#: Интервал поллинга по умолчанию (секунды).
DEFAULT_POLL_INTERVAL = 1.0


def _has_watchfiles() -> bool:
    """Доступен ли ``watchfiles`` (импортируется ли пакет)."""
    try:
        import watchfiles  # noqa: F401
    except ImportError:
        return False
    return True


def watching_backend() -> str:
    """Имя активного бэкенда слежения: ``"watchfiles"`` или ``"polling"``."""
    return "watchfiles" if _has_watchfiles() else "polling"


def _iter_files(paths: tuple[Path, ...]) -> Iterator[Path]:
    """Перечислить файлы под ``paths`` (каталоги — рекурсивно)."""
    for path in paths:
        if path.is_dir():
            yield from (p for p in path.rglob("*") if p.is_file())
        elif path.is_file():
            yield path


def _snapshot(paths: tuple[Path, ...]) -> dict[str, tuple[float, int]]:
    """Снимок состояния: путь -> (mtime, размер). Недоступные файлы пропущены."""
    snap: dict[str, tuple[float, int]] = {}
    for file in _iter_files(paths):
        try:
            st = file.stat()
        except OSError:
            continue
        snap[str(file)] = (st.st_mtime, st.st_size)
    return snap


def _diff(prev: dict[str, tuple[float, int]], cur: dict[str, tuple[float, int]]) -> set[str]:
    """Множество путей, отличающихся между снимками (добавлено/удалено/изменено)."""
    changed = set(prev) ^ set(cur)
    for path in set(prev) & set(cur):
        if prev[path] != cur[path]:
            changed.add(path)
    return changed


def iter_changes(*paths: Path, poll_interval: float = DEFAULT_POLL_INTERVAL) -> Iterator[set[str]]:
    """Итерировать наборы изменившихся путей под ``paths``.

    Бесконечный итератор: на каждое изменение отдаёт множество путей.
    Если есть ``watchfiles`` — делегирует ему (мгновенно); иначе —
    stdlib-поллинг с интервалом ``poll_interval``. ``KeyboardInterrupt``
    (Ctrl+C) пробрасывается наружу — его ловит команда ``watch``.

    :param paths: файлы и/или каталоги для слежения.
    :param poll_interval: интервал поллинга (только для stdlib-бэкенда).
    """
    if _has_watchfiles():
        from watchfiles import watch

        for changes in watch(*[str(p) for p in paths]):
            # watchfiles отдаёт set[(Change, str)] — нормализуем к путям.
            yield {item[1] if isinstance(item, tuple) else str(item) for item in changes}
        return

    tracked = tuple(paths)
    previous = _snapshot(tracked)
    while True:
        time.sleep(poll_interval)
        current = _snapshot(tracked)
        changed = _diff(previous, current)
        if changed:
            previous = current
            yield changed


__all__ = ["DEFAULT_POLL_INTERVAL", "iter_changes", "watching_backend"]
