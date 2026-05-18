"""Обёртка SDK ``ui.bulletin.BulletinHelper``.

На устройстве используется и ре-экспортируется настоящий
``BulletinHelper`` exteraGram; вне приложения — функциональный рекордер с
тем же интерфейсом: каждый показ фиксируется в ``BulletinHelper.shown``
(для проверок в тестах). На устройстве всегда работает настоящий SDK.
Зависит только от стандартной библиотеки и SDK.
"""

from __future__ import annotations

from typing import Any, ClassVar

try:  # pragma: no cover - ветка выполняется только на устройстве
    from ui.bulletin import BulletinHelper
except Exception:  # pragma: no cover - ветка для обычного Python

    class BulletinHelper:
        """Офлайн-рекордер ``BulletinHelper`` с полным интерфейсом SDK.

        Константы длительности и сигнатуры ``show_*`` повторяют документацию
        bulletin-helper. Все показы фиксируются в :attr:`shown`.
        """

        DURATION_SHORT = 1500
        DURATION_LONG = 2750
        DURATION_PROLONG = 5000

        #: Журнал показанных офлайн bulletin'ов: list[tuple].
        shown: ClassVar[list[tuple[Any, ...]]] = []

        @classmethod
        def _record(cls, name: str, *args: Any) -> None:
            cls.shown.append((name, *args))

        @classmethod
        def show_info(cls, message: str, fragment: Any = None) -> None:
            """Показать info-bulletin."""
            cls._record("info", message, fragment)

        @classmethod
        def show_error(cls, message: str, fragment: Any = None) -> None:
            """Показать error-bulletin."""
            cls._record("error", message, fragment)

        @classmethod
        def show_success(cls, message: str, fragment: Any = None) -> None:
            """Показать success-bulletin."""
            cls._record("success", message, fragment)

        @classmethod
        def show_simple(
            cls, text: str, icon_res_id: int, fragment: Any = None
        ) -> None:
            """Однострочный bulletin с кастомной анимацией."""
            cls._record("simple", text, icon_res_id, fragment)

        @classmethod
        def show_two_line(
            cls,
            title: str,
            subtitle: str,
            icon_res_id: int,
            fragment: Any = None,
        ) -> None:
            """Двухстрочный bulletin (заголовок + подпись)."""
            cls._record("two_line", title, subtitle, icon_res_id, fragment)

        @classmethod
        def show_with_button(
            cls,
            text: str,
            icon_res_id: int,
            button_text: str,
            on_click: Any,
            fragment: Any = None,
            duration: int = DURATION_PROLONG,
        ) -> None:
            """Bulletin с кнопкой-действием."""
            cls._record(
                "with_button", text, icon_res_id, button_text, on_click,
                fragment, duration,
            )

        @classmethod
        def show_undo(
            cls,
            text: str,
            on_undo: Any,
            on_action: Any = None,
            subtitle: str | None = None,
            fragment: Any = None,
        ) -> None:
            """Bulletin со сценарием отмены."""
            cls._record("undo", text, on_undo, on_action, subtitle, fragment)

        @classmethod
        def show_copied_to_clipboard(
            cls, message: str | None = None, fragment: Any = None
        ) -> None:
            """Bulletin «скопировано в буфер обмена»."""
            cls._record("copied_to_clipboard", message, fragment)

        @classmethod
        def show_link_copied(
            cls, is_private_link_info: bool = False, fragment: Any = None
        ) -> None:
            """Bulletin «ссылка скопирована»."""
            cls._record("link_copied", is_private_link_info, fragment)

        @classmethod
        def show_file_saved_to_gallery(
            cls, is_video: bool = False, amount: int = 1, fragment: Any = None
        ) -> None:
            """Bulletin «файл сохранён в галерею»."""
            cls._record("file_saved_to_gallery", is_video, amount, fragment)

        @classmethod
        def show_file_saved_to_downloads(
            cls,
            file_type_enum_name: str = "UNKNOWN",
            amount: int = 1,
            fragment: Any = None,
        ) -> None:
            """Bulletin «файл сохранён в загрузки»."""
            cls._record(
                "file_saved_to_downloads", file_type_enum_name, amount, fragment
            )


__all__ = ["BulletinHelper"]
