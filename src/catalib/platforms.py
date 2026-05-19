"""Детект окружения запуска CLI (ПК или Android: Termux/Pydroid).

catalib запускается и с ПК, и на самом устройстве, где работает
exteraGram (Termux, Pydroid 3). На устройстве нет `adb` и не нужен
`adb forward` (dev server слушает `127.0.0.1:42690`, а процесс уже на
устройстве), `watchfiles` не ставится без Rust, а системные бинарники
(`logcat`) вызываются напрямую. Команды спрашивают этот модуль о среде,
а не дублируют эвристику. Обоснование — ADR-0011.

Детект слоёный, потому что единого надёжного признака нет:

- `sys.platform == "android"` — Python 3.13+ (в т. ч. свежий Termux);
- `ANDROID_ROOT` и `ANDROID_DATA` в окружении — классический признак
  Android-Python (старый Termux, Pydroid с Python 3.11/3.9);
- наличие `/system` — файловый маркер Android.

Функции без сайд-эффектов и без кеша: окружение читается при каждом
вызове, чтобы детект был подменяем в тестах.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

#: Возможные значения :func:`android_flavor` (плюс пустая строка — не Android).
TERMUX = "termux"
PYDROID = "pydroid"
GENERIC_ANDROID = "android"


def _android_fs() -> bool:
    """Файловый маркер Android: каталог ``/system`` с типичным содержимым.

    Вынесено отдельной функцией, чтобы тесты подменяли её детерминированно
    (на ПК ``/system`` отсутствует, на Android — есть).
    """
    return Path("/system/build.prop").exists() or Path("/system/bin").is_dir()


def is_android() -> bool:
    """Запущены ли мы на Android (Termux, Pydroid или иной Android-Python).

    :returns: ``True`` на устройстве; ``False`` на обычном ПК.
    """
    if sys.platform == "android":
        return True
    env = os.environ
    if env.get("ANDROID_ROOT") and env.get("ANDROID_DATA"):
        return True
    return _android_fs()


def _looks_like_pydroid() -> bool:
    """Эвристика Pydroid 3: пакет ``ru.iiec.pydroid`` в путях/окружении."""
    if Path("/data/data/ru.iiec.pydroid3").exists():
        return True
    haystack = " ".join(
        (
            sys.executable or "",
            sys.prefix,
            sys.base_prefix,
            os.environ.get("HOME", ""),
            os.environ.get("PYTHONHOME", ""),
        )
    ).lower()
    return "pydroid" in haystack or "ru.iiec" in haystack


def _looks_like_termux() -> bool:
    """Эвристика Termux: ``TERMUX_VERSION`` либо пакет ``com.termux``."""
    if os.environ.get("TERMUX_VERSION"):
        return True
    if "com.termux" in os.environ.get("PREFIX", ""):
        return True
    return Path("/data/data/com.termux").exists()


def android_flavor() -> str:
    """Разновидность Android-окружения.

    :returns: :data:`TERMUX`, :data:`PYDROID`, :data:`GENERIC_ANDROID`
        либо ``""`` (не Android). Используется для подсказок и
        диагностики; на корректность деплоя влияет только факт Android.
    """
    if not is_android():
        return ""
    # Termux проверяется раньше: у него есть полноценный subprocess, и
    # это самый частый сценарий on-device разработки.
    if _looks_like_termux():
        return TERMUX
    if _looks_like_pydroid():
        return PYDROID
    return GENERIC_ANDROID


def should_use_adb(explicit: bool | None = None) -> bool:
    """Нужно ли использовать ``adb`` для связи с устройством.

    :param explicit: явный выбор пользователя (флаг ``--adb/--no-adb``);
        ``None`` — авто.
    :returns: при ``explicit is not None`` — само значение; иначе
        ``adb`` нужен только не на Android (на устройстве подключаемся к
        dev server напрямую, см. ADR-0011).
    """
    if explicit is not None:
        return explicit
    return not is_android()


def describe_environment() -> str:
    """Человекочитаемое имя среды (для ``doctor`` и подсказок)."""
    flavor = android_flavor()
    if flavor == TERMUX:
        return "Termux (Android)"
    if flavor == PYDROID:
        return "Pydroid 3 (Android)"
    if flavor == GENERIC_ANDROID:
        return "Android"
    return f"ПК ({sys.platform})"


__all__ = [
    "GENERIC_ANDROID",
    "PYDROID",
    "TERMUX",
    "android_flavor",
    "describe_environment",
    "is_android",
    "should_use_adb",
]
