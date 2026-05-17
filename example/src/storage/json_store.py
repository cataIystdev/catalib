"""Обобщённое JSON-хранилище на файловой системе."""

from __future__ import annotations

import json
import os
from typing import Any


class JsonStore:
    """Чтение/запись JSON-документа по фиксированному пути.

    :param path: путь к файлу хранилища.
    """

    def __init__(self, path: str) -> None:
        self._path = path

    def load(self, default: Any) -> Any:
        """Загрузить документ или вернуть ``default`` при отсутствии/ошибке."""
        if not os.path.isfile(self._path):
            return default
        try:
            with open(self._path, encoding="utf-8") as handle:
                return json.load(handle)
        except (OSError, ValueError):
            return default

    def save(self, data: Any) -> None:
        """Сохранить документ, создав родительские каталоги при необходимости."""
        parent = os.path.dirname(self._path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        tmp_path = self._path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
        os.replace(tmp_path, self._path)
