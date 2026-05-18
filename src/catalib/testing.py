"""Помощники для офлайн-тестов плагинов (без устройства и SDK).

Тестировать хук/пункт меню «по-настоящему» мешает шаблон: нужно собрать
фейковые ``params``/``context``, создать плагин и вызвать
``on_plugin_load`` (иначе хуки/меню не зарегистрированы). Этот модуль
убирает шаблон: :func:`make_params`, :func:`make_context` и
:class:`PluginHarness` дают вызвать обработчики плагина в обычном pytest.

Модуль pytest-нейтрален (только stdlib + офлайн-заглушки
:mod:`catalib.support`), ничего не регистрирует глобально и **не
вендорится** в собранный плагин — он импортируется только тестами,
никогда из ``src/plugin.py``.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from catalib.support import CatalibPlugin
from catalib.support.sdk import HookResult


def make_params(message: str = "", **fields: Any) -> SimpleNamespace:
    """Собрать объект ``params`` хука исходящих сообщений.

    SDK передаёт обработчику объект с атрибутами (``message`` и др.).
    Офлайн достаточно :class:`types.SimpleNamespace` — атрибуты можно и
    читать, и присваивать (хук обычно пишет ``params.message``).

    :param message: текст сообщения (атрибут ``message``).
    :param fields: любые дополнительные атрибуты (``peer`` и т. п.).
    """
    return SimpleNamespace(message=message, **fields)


def make_context(**fields: Any) -> dict[str, Any]:
    """Собрать ``context``-словарь обработчика пункта меню.

    SDK передаёт обработчику меню ``context: dict``. Офлайн это просто
    словарь с переданными ключами.
    """
    return dict(fields)


class PluginHarness:
    """Загруженный плагин + удобные вызовы его обработчиков.

    :meth:`load` создаёт плагин, проставляет настройки и вызывает
    ``on_plugin_load`` (хуки/меню регистрируются на офлайн-заглушке
    ``BasePlugin``). Дальше :meth:`send_message`/:meth:`click_menu`
    вызывают обработчики так же, как это сделал бы SDK.
    """

    def __init__(self, plugin: CatalibPlugin) -> None:
        self.plugin = plugin
        #: ``params`` последнего :meth:`send_message` (для проверки мутаций).
        self.last_params: SimpleNamespace | None = None

    @classmethod
    def load(
        cls,
        plugin_cls: type[CatalibPlugin],
        *,
        settings: dict[str, Any] | None = None,
        **extra_settings: Any,
    ) -> PluginHarness:
        """Создать плагин, применить настройки и вызвать ``on_plugin_load``.

        :param plugin_cls: класс плагина (подкласс ``CatalibPlugin``).
        :param settings: словарь начальных настроек (``get_setting``).
        :param extra_settings: настройки как именованные аргументы (удобно
            для простых ключей); объединяются поверх ``settings``.
        """
        plugin = plugin_cls()
        for key, value in {**(settings or {}), **extra_settings}.items():
            plugin.set_setting(key, value)
        plugin.on_plugin_load()
        return cls(plugin)

    @property
    def registered_hooks(self) -> list[Any]:
        """Зафиксированные вызовы регистрации хуков (как в SDK-заглушке)."""
        return list(self.plugin.registered_hooks)

    @property
    def menu_items(self) -> list[Any]:
        """Зарегистрированные пункты меню (объекты ``MenuItemData``)."""
        return list(self.plugin.registered_menu_items)

    @property
    def logged(self) -> list[str]:
        """Строки, переданные ``self.log(...)`` плагином."""
        return list(self.plugin.logged)

    def send_message(self, message: str = "", *, account: int = 0, **fields: Any) -> HookResult:
        """Вызвать ``@hook.send_message``-обработчик(и) плагина.

        Собирает ``params`` (доступен затем как :attr:`last_params`),
        вызывает все помеченные ``send_message`` методы (как SDK) и
        возвращает последний :class:`HookResult`.

        :raises LookupError: если в плагине нет ``@hook.send_message``.
        """
        params = make_params(message, **fields)
        self.last_params = params
        result: HookResult | None = None
        for attr_name, spec in self.plugin._catalib_hooks:
            if spec.kind == "send_message":
                result = getattr(self.plugin, attr_name)(account, params)
        if result is None:
            raise LookupError("в плагине нет метода с @hook.send_message")
        return result

    def click_menu(
        self, text: str | None = None, *, context: dict[str, Any] | None = None, **ctx: Any
    ) -> Any:
        """Вызвать обработчик пункта меню (как клик в SDK).

        :param text: подпись пункта; ``None`` — первый зарегистрированный.
        :param context: готовый ``context``-словарь; иначе собирается из
            ``ctx`` через :func:`make_context`.
        :raises LookupError: если подходящий пункт меню не найден.
        """
        for data in self.menu_items:
            if text is None or getattr(data, "text", None) == text:
                payload = context if context is not None else make_context(**ctx)
                return data.on_click(payload)
        raise LookupError(f"пункт меню не найден: {text!r}")


def load_plugin(
    plugin_cls: type[CatalibPlugin],
    *,
    settings: dict[str, Any] | None = None,
    **extra_settings: Any,
) -> PluginHarness:
    """Краткий синоним :meth:`PluginHarness.load`."""
    return PluginHarness.load(plugin_cls, settings=settings, **extra_settings)


__all__ = ["PluginHarness", "load_plugin", "make_context", "make_params"]
