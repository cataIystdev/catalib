"""Обёртки модуля SDK ``hook_utils`` — рефлексия Java-полей.

На устройстве вызываются настоящие функции ``hook_utils``; вне приложения —
безопасные офлайн-заглушки с тем же контрактом (геттеры возвращают ``None``,
сеттеры — ``False``), чтобы код плагина импортировался и тестировался без
устройства. ``find_class`` ре-экспортируется из :mod:`catalib.support.sdk`
(единая точка адаптации, ADR-0003).

Рефлексия хрупка при обновлении приложения: вызовы обёрнуты в ``try/except``
и возвращают безопасные значения, как требует документация hook-utils.
Зависит только от стандартной библиотеки и SDK.
"""

from __future__ import annotations

from typing import Any

from catalib.support.sdk import find_class


def get_private_field(obj: Any, field_name: str) -> Any:
    """Прочитать значение приватного/публичного поля экземпляра.

    :param obj: Java-объект.
    :param field_name: имя поля.
    :returns: значение поля либо ``None`` (офлайн или при ошибке).
    """
    try:  # pragma: no cover - на устройстве
        from hook_utils import get_private_field as _get

        return _get(obj, field_name)
    except Exception:
        return None


def set_private_field(obj: Any, field_name: str, new_value: Any) -> bool:
    """Записать значение приватного/публичного поля экземпляра.

    :param obj: Java-объект.
    :param field_name: имя поля.
    :param new_value: новое значение.
    :returns: ``True`` при успехе, иначе ``False`` (офлайн — ``False``).
    """
    try:  # pragma: no cover - на устройстве
        from hook_utils import set_private_field as _set

        return bool(_set(obj, field_name, new_value))
    except Exception:
        return False


def get_static_private_field(clazz: Any, field_name: str) -> Any:
    """Прочитать значение статического приватного/публичного поля класса.

    :param clazz: Java-``Class``.
    :param field_name: имя статического поля.
    :returns: значение либо ``None`` (офлайн или при ошибке).
    """
    try:  # pragma: no cover - на устройстве
        from hook_utils import get_static_private_field as _get

        return _get(clazz, field_name)
    except Exception:
        return None


def set_static_private_field(clazz: Any, field_name: str, new_value: Any) -> bool:
    """Записать значение статического приватного/публичного поля класса.

    :param clazz: Java-``Class``.
    :param field_name: имя статического поля.
    :param new_value: новое значение.
    :returns: ``True`` при успехе, иначе ``False`` (офлайн — ``False``).
    """
    try:  # pragma: no cover - на устройстве
        from hook_utils import set_static_private_field as _set

        return bool(_set(clazz, field_name, new_value))
    except Exception:
        return False


__all__ = [
    "find_class",
    "get_private_field",
    "get_static_private_field",
    "set_private_field",
    "set_static_private_field",
]
