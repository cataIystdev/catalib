"""Определение каталога данных плагина на устройстве.

Каталог плагинов доступен для записи (подтверждено зондом catalib).
В офлайн-тестах ``get_plugins_dir`` из catalib.support возвращает временный
каталог, поэтому модуль безопасен и вне exteraGram.
"""

from __future__ import annotations

import os

from catalib.support import get_plugins_dir

from ..config import DATA_DIR_NAME


def data_dir() -> str:
    """Вернуть (создав при необходимости) каталог данных плагина."""
    path = os.path.join(get_plugins_dir(), DATA_DIR_NAME)
    os.makedirs(path, exist_ok=True)
    return path
