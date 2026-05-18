"""Типизированные декларативные настройки плагина.

Описание настроек не зависит от наличия SDK: на устройстве элементы
конвертируются в классы ``ui.settings`` exteraGram, в офлайн-тестах остаются
самодостаточными объектами с теми же полями.

Полный паритет с публичным SDK ``ui.settings`` (ADR-0006): компоненты
``header``, ``divider``, ``switch``, ``selector``, ``text_input`` (Input),
``edit_text`` (EditText), ``text`` (кликабельный Text), ``custom`` со всеми
параметрами SDK (``on_click``, ``on_change``, ``icon``, ``accent``, ``red``,
``link_alias``, ``create_sub_fragment``, ``multiline``, ``max_length``,
``mask``).

Расширения строго аддитивны: прежние позиционные сигнатуры ``header``,
``switch``, ``text_input``, ``text`` сохранены, а новые параметры — только
keyword-only и со «незаданным» значением по умолчанию, поэтому для прежнего
кода итоговый ``params`` (и вызов ``ui.settings``) не меняется.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

#: Поддерживаемые типы элементов настроек и соответствующие классы ui.settings.
_SDK_CLASS_BY_KIND = {
    "header": "Header",
    "divider": "Divider",
    "switch": "Switch",
    "selector": "Selector",
    "input": "Input",
    "edittext": "EditText",
    "text": "Text",
    "custom": "Custom",
}


@dataclass(frozen=True, slots=True)
class SettingItem:
    """Один элемент настроек плагина.

    :param kind: тип элемента — ключ из :data:`_SDK_CLASS_BY_KIND`
        (``header`` | ``divider`` | ``switch`` | ``selector`` | ``input`` |
        ``edittext`` | ``text`` | ``custom``).
    :param params: именованные параметры, передаваемые классу ``ui.settings``.
    """

    kind: str
    params: dict[str, Any] = field(default_factory=dict)

    def build(self) -> Any:
        """Построить объект ``ui.settings`` (на устройстве) либо вернуть себя.

        В офлайн-окружении SDK недоступен — возвращается сам элемент, что
        удобно для модульных тестов.
        """
        try:  # pragma: no cover - выполняется только на устройстве
            from ui import settings as sdk_settings

            sdk_class = getattr(sdk_settings, _SDK_CLASS_BY_KIND[self.kind])
            return sdk_class(**self.params)
        except Exception:
            return self


def header(text: str) -> SettingItem:
    """Заголовок секции настроек.

    :param text: текст заголовка.
    """
    return SettingItem("header", {"text": text})


def divider(text: str = "") -> SettingItem:
    """Разделитель с необязательной подписью.

    :param text: необязательная подпись разделителя; если пусто — без неё.
    """
    params: dict[str, Any] = {}
    if text:
        params["text"] = text
    return SettingItem("divider", params)


def switch(
    key: str,
    text: str,
    default: bool = False,
    subtext: str = "",
    *,
    icon: str = "",
    on_change: Callable[..., Any] | None = None,
    link_alias: str = "",
) -> SettingItem:
    """Переключатель булевой настройки.

    :param key: ключ настройки (``get_setting``/``set_setting``).
    :param text: подпись переключателя.
    :param default: значение по умолчанию.
    :param subtext: необязательная подпись под текстом.
    :param icon: необязательная иконка (drawable).
    :param on_change: необязательный обработчик изменения значения.
    :param link_alias: необязательный алиас для ссылки на настройку.
    """
    params: dict[str, Any] = {"key": key, "text": text, "default": default}
    if subtext:
        params["subtext"] = subtext
    if icon:
        params["icon"] = icon
    if on_change is not None:
        params["on_change"] = on_change
    if link_alias:
        params["link_alias"] = link_alias
    return SettingItem("switch", params)


def selector(
    key: str,
    text: str,
    default: int,
    items: list[str],
    *,
    icon: str = "",
    on_change: Callable[..., Any] | None = None,
) -> SettingItem:
    """Выпадающий список (выбор одного значения из набора).

    :param key: ключ настройки; хранит индекс выбранного пункта.
    :param text: подпись селектора.
    :param default: индекс выбранного по умолчанию пункта.
    :param items: непустой список подписей пунктов.
    :param icon: необязательная иконка (drawable).
    :param on_change: необязательный обработчик изменения значения.
    :raises ValueError: если ``items`` не является непустым списком строк.
    """
    if not isinstance(items, list) or not items:
        raise ValueError("items селектора должен быть непустым списком")
    if not all(isinstance(it, str) for it in items):
        raise ValueError("items селектора должен содержать только строки")
    params: dict[str, Any] = {
        "key": key,
        "text": text,
        "default": default,
        "items": items,
    }
    if icon:
        params["icon"] = icon
    if on_change is not None:
        params["on_change"] = on_change
    return SettingItem("selector", params)


def text_input(
    key: str,
    text: str,
    default: str = "",
    subtext: str = "",
    icon: str = "",
    *,
    on_change: Callable[..., Any] | None = None,
    link_alias: str = "",
) -> SettingItem:
    """Однострочное текстовое поле ввода (``ui.settings.Input``).

    :param key: ключ настройки.
    :param text: подпись поля.
    :param default: значение по умолчанию.
    :param subtext: необязательная подпись под текстом.
    :param icon: необязательная иконка (drawable).
    :param on_change: необязательный обработчик изменения значения.
    :param link_alias: необязательный алиас для ссылки на настройку.
    """
    params: dict[str, Any] = {"key": key, "text": text, "default": default}
    if subtext:
        params["subtext"] = subtext
    if icon:
        params["icon"] = icon
    if on_change is not None:
        params["on_change"] = on_change
    if link_alias:
        params["link_alias"] = link_alias
    return SettingItem("input", params)


def edit_text(
    key: str,
    hint: str,
    default: str = "",
    *,
    multiline: bool = False,
    max_length: int = 0,
    mask: str = "",
    on_change: Callable[..., Any] | None = None,
) -> SettingItem:
    """Многострочное текстовое поле (``ui.settings.EditText``).

    :param key: ключ настройки.
    :param hint: текст-подсказка (placeholder).
    :param default: значение по умолчанию; добавляется при непустом значении.
    :param multiline: разрешить многострочный ввод.
    :param max_length: ограничение длины (>0 — добавляется в параметры).
    :param mask: необязательная маска ввода.
    :param on_change: необязательный обработчик изменения значения.
    """
    params: dict[str, Any] = {"key": key, "hint": hint}
    if default:
        params["default"] = default
    if multiline:
        params["multiline"] = True
    if max_length:
        params["max_length"] = max_length
    if mask:
        params["mask"] = mask
    if on_change is not None:
        params["on_change"] = on_change
    return SettingItem("edittext", params)


def text(
    text: str,
    subtext: str = "",
    icon: str = "",
    *,
    accent: bool = False,
    red: bool = False,
    on_click: Callable[..., Any] | None = None,
    create_sub_fragment: Callable[..., Any] | None = None,
    link_alias: str = "",
) -> SettingItem:
    """Информационная или кликабельная строка (``ui.settings.Text``).

    Первоклассный способ сделать строку настроек кликабельной — передать
    ``on_click``; ручной перебор API клика в плагине больше не нужен.

    :param text: основной текст строки.
    :param subtext: необязательная подпись под текстом.
    :param icon: необязательная иконка (drawable).
    :param accent: выделить акцентным цветом.
    :param red: выделить красным (деструктивное действие).
    :param on_click: обработчик клика по строке.
    :param create_sub_fragment: фабрика вложенного экрана настроек.
    :param link_alias: необязательный алиас для ссылки на настройку.
    """
    params: dict[str, Any] = {"text": text}
    if subtext:
        params["subtext"] = subtext
    if icon:
        params["icon"] = icon
    if accent:
        params["accent"] = True
    if red:
        params["red"] = True
    if on_click is not None:
        params["on_click"] = on_click
    if create_sub_fragment is not None:
        params["create_sub_fragment"] = create_sub_fragment
    if link_alias:
        params["link_alias"] = link_alias
    return SettingItem("text", params)


def custom(
    *,
    item: Any = None,
    view: Any = None,
    factory: Callable[..., Any] | None = None,
    factory_args: Any = None,
    on_click: Callable[..., Any] | None = None,
) -> SettingItem:
    """Кастомная строка настроек (``ui.settings.Custom``).

    Источник содержимого задаётся одним из ``item`` / ``view`` / ``factory``.

    :param item: готовый элемент строки.
    :param view: готовое Android-``View``.
    :param factory: фабрика, создающая ``View``.
    :param factory_args: аргументы фабрики.
    :param on_click: необязательный обработчик клика.
    :raises ValueError: если не задан ни ``item``, ни ``view``, ни ``factory``.
    """
    if item is None and view is None and factory is None:
        raise ValueError("custom требует один из аргументов: item, view или factory")
    params: dict[str, Any] = {}
    if item is not None:
        params["item"] = item
    if view is not None:
        params["view"] = view
    if factory is not None:
        params["factory"] = factory
    if factory_args is not None:
        params["factory_args"] = factory_args
    if on_click is not None:
        params["on_click"] = on_click
    return SettingItem("custom", params)
