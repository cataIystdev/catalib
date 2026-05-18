"""Обёртка SDK ``ui.alert.AlertDialogBuilder``.

На устройстве используется и ре-экспортируется настоящий
``AlertDialogBuilder`` exteraGram; вне приложения — функциональный
chainable-рекордер с тем же интерфейсом: каждый вызов фиксируется в
``calls`` (для проверок в тестах) и возвращает ``self`` (как builder), а
``get_dialog``/``get_button`` офлайн возвращают ``None``. На устройстве
всегда работает настоящий SDK. Зависит только от стандартной библиотеки
и SDK.
"""

from __future__ import annotations

from typing import Any

try:  # pragma: no cover - ветка выполняется только на устройстве
    from ui.alert import AlertDialogBuilder
except Exception:  # pragma: no cover - ветка для обычного Python

    class AlertDialogBuilder:
        """Офлайн-рекордер ``AlertDialogBuilder`` с полным интерфейсом SDK.

        Константы и сигнатуры методов повторяют документацию
        alert-dialog-builder. Каждый метод-сеттер фиксирует вызов в
        :attr:`calls` и возвращает ``self`` для цепочечного построения.
        """

        # Типы диалога.
        ALERT_TYPE_MESSAGE = 0
        ALERT_TYPE_LOADING = 1
        ALERT_TYPE_SPINNER = 2
        # Идентификаторы кнопок (значения как у Android DialogInterface).
        BUTTON_POSITIVE = -1
        BUTTON_NEGATIVE = -2

        def __init__(
            self,
            context: Any,
            progress_style: int = ALERT_TYPE_MESSAGE,
            resources_provider: Any = None,
        ) -> None:
            self.context = context
            self.progress_style = progress_style
            self.resources_provider = resources_provider
            self.calls: list[tuple[Any, ...]] = []
            self._shown = False
            self._dismissed = False

        def _record(self, name: str, *args: Any) -> AlertDialogBuilder:
            self.calls.append((name, *args))
            return self

        # --- Содержимое ---
        def set_title(self, title: str) -> AlertDialogBuilder:
            """Задать заголовок."""
            return self._record("set_title", title)

        def set_message(self, message: str) -> AlertDialogBuilder:
            """Задать текст сообщения."""
            return self._record("set_message", message)

        def set_message_text_view_clickable(self, clickable: bool) -> AlertDialogBuilder:
            """Сделать текст сообщения кликабельным."""
            return self._record("set_message_text_view_clickable", clickable)

        def set_view(self, view: Any, height: int = -2) -> AlertDialogBuilder:
            """Задать кастомное содержимое."""
            return self._record("set_view", view, height)

        def set_items(
            self, items: list[str], listener: Any = None, icons: Any = None
        ) -> AlertDialogBuilder:
            """Задать список выбираемых пунктов."""
            return self._record("set_items", items, listener, icons)

        # --- Кнопки ---
        def set_positive_button(
            self, text: str, listener: Any = None
        ) -> AlertDialogBuilder:
            """Положительная кнопка."""
            return self._record("set_positive_button", text, listener)

        def set_negative_button(
            self, text: str, listener: Any = None
        ) -> AlertDialogBuilder:
            """Отрицательная кнопка."""
            return self._record("set_negative_button", text, listener)

        def set_neutral_button(
            self, text: str, listener: Any = None
        ) -> AlertDialogBuilder:
            """Нейтральная кнопка."""
            return self._record("set_neutral_button", text, listener)

        def make_button_red(self, button_type: int) -> AlertDialogBuilder:
            """Окрасить кнопку в красный (деструктив)."""
            return self._record("make_button_red", button_type)

        # --- Слушатели ---
        def set_on_back_button_listener(self, listener: Any = None) -> AlertDialogBuilder:
            """Обработчик кнопки «назад»."""
            return self._record("set_on_back_button_listener", listener)

        def set_on_dismiss_listener(self, listener: Any = None) -> AlertDialogBuilder:
            """Обработчик закрытия."""
            return self._record("set_on_dismiss_listener", listener)

        def set_on_cancel_listener(self, listener: Any = None) -> AlertDialogBuilder:
            """Обработчик отмены."""
            return self._record("set_on_cancel_listener", listener)

        # --- Внешний вид и поведение ---
        def set_top_image(self, res_id: int, background_color: int) -> AlertDialogBuilder:
            """Изображение в шапке."""
            return self._record("set_top_image", res_id, background_color)

        def set_top_drawable(
            self, drawable: Any, background_color: int
        ) -> AlertDialogBuilder:
            """Drawable в шапке."""
            return self._record("set_top_drawable", drawable, background_color)

        def set_top_animation(
            self,
            res_id: int,
            size: int,
            auto_repeat: bool,
            background_color: int,
            layer_colors: Any = None,
        ) -> AlertDialogBuilder:
            """Lottie-анимация в шапке."""
            return self._record(
                "set_top_animation",
                res_id,
                size,
                auto_repeat,
                background_color,
                layer_colors,
            )

        def set_dim_enabled(self, enabled: bool) -> AlertDialogBuilder:
            """Затемнение фона."""
            return self._record("set_dim_enabled", enabled)

        def set_dialog_button_color_key(self, theme_key: int) -> AlertDialogBuilder:
            """Цветовой ключ кнопок из темы."""
            return self._record("set_dialog_button_color_key", theme_key)

        def set_blurred_background(
            self, blur: bool, blur_behind_if_possible: bool = True
        ) -> AlertDialogBuilder:
            """Размытие фона."""
            return self._record(
                "set_blurred_background", blur, blur_behind_if_possible
            )

        def set_cancelable(self, cancelable: bool) -> AlertDialogBuilder:
            """Можно ли отменить."""
            return self._record("set_cancelable", cancelable)

        def set_canceled_on_touch_outside(self, cancel: bool) -> AlertDialogBuilder:
            """Отмена по тапу вне диалога."""
            return self._record("set_canceled_on_touch_outside", cancel)

        # --- Прогресс ---
        def set_progress(self, progress: int) -> AlertDialogBuilder:
            """Значение прогресс-бара."""
            return self._record("set_progress", progress)

        # --- Жизненный цикл ---
        def create(self) -> AlertDialogBuilder:
            """Создать диалог (офлайн — фиксирует вызов)."""
            return self._record("create")

        def show(self) -> AlertDialogBuilder:
            """Показать диалог (офлайн — фиксирует вызов)."""
            self._shown = True
            return self._record("show")

        def dismiss(self) -> None:
            """Закрыть диалог (офлайн — фиксирует вызов)."""
            self._dismissed = True
            self.calls.append(("dismiss",))

        def get_dialog(self) -> Any:
            """Нижележащий ``AlertDialog`` (офлайн — ``None``)."""
            return None

        def get_button(self, button_type: int) -> Any:
            """``View`` кнопки (офлайн — ``None``)."""
            return None


__all__ = ["AlertDialogBuilder"]
