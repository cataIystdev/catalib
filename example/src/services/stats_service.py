"""Учёт количества использований команд."""

from __future__ import annotations

import os

from ..storage.json_store import JsonStore


class StatsService:
    """Счётчик вызовов команд, персистентный в ``<base_dir>/stats.json``.

    :param base_dir: каталог данных плагина.
    """

    def __init__(self, base_dir: str) -> None:
        self._store = JsonStore(os.path.join(base_dir, "stats.json"))

    def _read(self) -> dict[str, int]:
        data = self._store.load(default={})
        if not isinstance(data, dict):
            return {}
        return {str(k): int(v) for k, v in data.items() if isinstance(v, int)}

    def increment(self, name: str) -> None:
        """Увеличить счётчик команды ``name`` на единицу."""
        data = self._read()
        data[name] = data.get(name, 0) + 1
        self._store.save(data)

    def summary(self) -> str:
        """Текстовая сводка по убыванию частоты."""
        data = self._read()
        if not data:
            return "статистика пуста"
        rows = sorted(data.items(), key=lambda kv: (-kv[1], kv[0]))
        lines = ["Статистика команд:"]
        lines += [f"{name}: {count}" for name, count in rows]
        return "\n".join(lines)
