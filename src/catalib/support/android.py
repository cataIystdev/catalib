"""Обёртки модуля SDK ``android_utils``.

На устройстве используются настоящие интерфейс-обёртки exteraGram
(``R``, ``OnClickListener``, ``OnLongClickListener``, ``copy_to_clipboard``);
вне приложения — функциональные офлайн-заглушки, которые действительно
вызывают переданный callable (это полноценный офлайн-контракт для тестов,
а не пустышка; на устройстве всегда работает настоящий SDK).

``log`` и ``run_on_ui_thread`` ре-экспортируются из :mod:`catalib.support.sdk`
(единая точка адаптации, ADR-0003): там уже реализованы безопасный импорт и
fallback по аргументу задержки. Зависит только от стандартной библиотеки,
SDK exteraGram и встраиваемого периметра catalib.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from catalib.support.sdk import log, run_on_ui_thread

#: Записанные офлайн вызовы ``copy_to_clipboard`` (для проверок в тестах).
_clipboard_history: list[str] = []


try:  # pragma: no cover - ветка выполняется только на устройстве
    from android_utils import R
except Exception:  # pragma: no cover - ветка для обычного Python

    class R:
        """Офлайн-заглушка ``java.lang.Runnable`` из Python-callable.

        Хранит callable и вызывает его при ``run()`` либо при вызове
        экземпляра — этого достаточно для офлайн-тестов логики.
        """

        def __init__(self, fn: Callable[[], Any]) -> None:
            self.fn = fn

        def run(self) -> Any:
            """Выполнить обёрнутый callable."""
            return self.fn()

        def __call__(self) -> Any:
            return self.fn()


try:  # pragma: no cover - ветка выполняется только на устройстве
    from android_utils import OnClickListener
except Exception:  # pragma: no cover - ветка для обычного Python

    class OnClickListener:
        """Офлайн-заглушка ``View.OnClickListener``.

        Callable получает кликнутый ``View`` единственным аргументом.
        """

        def __init__(self, fn: Callable[[Any], Any]) -> None:
            self.fn = fn

        def onClick(self, view: Any = None) -> Any:
            """Сымитировать клик по ``view``."""
            return self.fn(view)

        def __call__(self, view: Any = None) -> Any:
            return self.fn(view)


try:  # pragma: no cover - ветка выполняется только на устройстве
    from android_utils import OnLongClickListener
except Exception:  # pragma: no cover - ветка для обычного Python

    class OnLongClickListener:
        """Офлайн-заглушка ``View.OnLongClickListener``.

        Callable получает ``View`` и возвращает ``bool``: ``True`` —
        событие поглощено, ``False`` — обработка продолжается.
        """

        def __init__(self, fn: Callable[[Any], bool]) -> None:
            self.fn = fn

        def onLongClick(self, view: Any = None) -> bool:
            """Сымитировать долгий клик по ``view``."""
            return bool(self.fn(view))

        def __call__(self, view: Any = None) -> bool:
            return bool(self.fn(view))


def copy_to_clipboard(text: str) -> None:
    """Скопировать строку в системный буфер обмена.

    На устройстве вызывает ``android_utils.copy_to_clipboard`` (та же
    стандартная всплывашка «скопировано»). Офлайн — записывает значение в
    :data:`_clipboard_history` и ничего не делает (для проверок в тестах).

    :param text: строка для копирования.
    """
    try:  # pragma: no cover - на устройстве
        from android_utils import copy_to_clipboard as _copy

        _copy(text)
    except Exception:
        _clipboard_history.append(text)


__all__ = [
    "OnClickListener",
    "OnLongClickListener",
    "R",
    "copy_to_clipboard",
    "log",
    "run_on_ui_thread",
]
