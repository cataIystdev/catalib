"""Декларативные Xposed-хуки методов Java.

Документированный паттерн exteraGram (см. шаблон ``xposed_demo``):
``find_class`` → ``getDeclaredMethod``/``getDeclaredConstructor`` →
``self.hook_method(method, MethodHook(), priority=...)`` → в
``on_plugin_unload`` ``self.unhook_method(handle)``. Это много шаблона и
типовая ошибка — забыть ``unhook``.

Здесь хук объявляется одним декоратором :func:`xposed` на методе плагина;
:class:`~catalib.support.plugin.CatalibPlugin` регистрирует его в
``on_plugin_load`` и снимает в ``on_plugin_unload`` автоматически. Все
ошибки рефлексии перехватываются и логируются (рефлексия хрупка при
обновлении приложения — pitfall #7), кадр загрузки не падает.

Слой не скрывает SDK: те же ``MethodHook``/``MethodReplacement``/
``HookFilter``/``find_class`` доступны напрямую через
:mod:`catalib.support.sdk`. Зависит только от стандартной библиотеки и SDK.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import catalib.support.sdk as sdk

#: Имя атрибута-маркера на методе-обработчике Xposed-хука.
XPOSED_ATTR = "__catalib_xposed__"

#: Допустимые фазы хука.
_PHASES = ("before", "after", "replace")


@dataclass(frozen=True, slots=True)
class XposedSpec:
    """Описание декларативного Xposed-хука, привязанного к методу плагина.

    :param class_fqn: полное имя Java-класса (``org.telegram.ui.ChatActivity``).
    :param method_name: имя метода; для конструктора игнорируется.
    :param phase: ``before`` | ``after`` | ``replace``.
    :param priority: приоритет хука (по умолчанию 10, как в SDK).
    :param is_constructor: хукать конструктор, а не метод.
    :param arg_types: типы аргументов для разрешения перегрузки —
        кортеж FQN-строк (резолвятся ``find_class``) либо уже готовых
        Java-``Class``; ``None`` — без уточнения (метод без перегрузок).
    :param filters: кортеж фильтров ``HookFilter`` (применяются через
        ``hook_filters`` к методу моста).
    """

    class_fqn: str
    method_name: str
    phase: str
    priority: int = 10
    is_constructor: bool = False
    arg_types: tuple[Any, ...] | None = None
    filters: tuple[Any, ...] = field(default_factory=tuple)


def xposed(
    class_fqn: str,
    method_name: str = "",
    *,
    phase: str = "after",
    priority: int = 10,
    is_constructor: bool = False,
    arg_types: tuple[Any, ...] | list[Any] | None = None,
    filters: tuple[Any, ...] | list[Any] = (),
) -> Callable[[Callable], Callable]:
    """Пометить метод плагина как обработчик Xposed-хука.

    Обработчик получает один аргумент ``param`` (``MethodHookParam`` SDK):
    ``param.thisObject``, ``param.args``, ``param.getResult()``,
    ``param.setResult(v)`` и т. д. Для ``phase="replace"`` возвращаемое
    значение обработчика становится результатом метода.

    :param class_fqn: полное имя Java-класса (непустая строка).
    :param method_name: имя метода; для конструктора можно опустить.
    :param phase: ``before`` (до оригинала), ``after`` (после) или
        ``replace`` (полная замена).
    :param priority: приоритет хука.
    :param is_constructor: хукать конструктор.
    :param arg_types: типы аргументов для разрешения перегрузки.
    :param filters: фильтры ``HookFilter`` (см. :mod:`catalib.support.sdk`).
    :raises ValueError: при пустом ``class_fqn``, неизвестной ``phase`` или
        пустом ``method_name`` для не-конструктора.
    """
    if not isinstance(class_fqn, str) or not class_fqn:
        raise ValueError("class_fqn должен быть непустой строкой")
    if phase not in _PHASES:
        raise ValueError(f"phase должен быть одним из {_PHASES}")
    if not is_constructor and (not isinstance(method_name, str) or not method_name):
        raise ValueError("method_name обязателен для хука метода (не конструктора)")

    spec = XposedSpec(
        class_fqn=class_fqn,
        method_name=method_name,
        phase=phase,
        priority=priority,
        is_constructor=is_constructor,
        arg_types=tuple(arg_types) if arg_types is not None else None,
        filters=tuple(filters),
    )

    def decorator(func: Callable) -> Callable:
        setattr(func, XPOSED_ATTR, spec)
        return func

    return decorator


def _make_bridge(handler: Callable[[Any], Any], phase: str, filters: tuple[Any, ...]) -> Any:
    """Построить объект-мост SDK, делегирующий в связанный метод плагина.

    Методы ``MethodHook``/``MethodReplacement`` получают ``self`` моста; сам
    обработчик плагина уже связан (``self`` плагина захвачен). Фильтры
    применяются к методу фазы через ``hook_filters`` ровно как в
    документации SDK (``@hook_filters(...) def before_hooked_method``).
    """

    def phase_call(_self: Any, param: Any) -> Any:
        return handler(param)

    if filters:
        phase_call = sdk.hook_filters(*filters)(phase_call)

    if phase == "replace":
        return type(
            "_CatalibReplaceHook",
            (sdk.MethodReplacement,),
            {"replace_hooked_method": phase_call},
        )()
    method_name = "before_hooked_method" if phase == "before" else "after_hooked_method"
    return type("_CatalibMethodHook", (sdk.MethodHook,), {method_name: phase_call})()


def _log(plugin: Any, message: str) -> None:
    """Записать диагностику Xposed-слоя.

    Предпочтительно через логгер плагина (есть и в SDK, и в офлайн-заглушке —
    диагностику видно в тестах); при его отсутствии — через модульный
    ``sdk.log`` (на устройстве уходит в ``android_utils.log``).
    """
    try:
        plugin.log(message)
    except Exception:
        sdk.log(message)


def _resolve_member(spec: XposedSpec) -> Any:
    """Найти Java-класс и нужный метод/конструктор по спецификации.

    :returns: объект метода/конструктора либо ``None``, если класс или тип
        аргумента не найдены (вне exteraGram ``find_class`` всегда ``None``).
    """
    cls_obj = sdk.find_class(spec.class_fqn)
    if cls_obj is None:
        return None
    resolved: list[Any] = []
    for arg in spec.arg_types or ():
        if isinstance(arg, str):
            arg_cls = sdk.find_class(arg)
            if arg_cls is None:
                return None
            resolved.append(arg_cls)
        else:
            resolved.append(arg)
    if spec.is_constructor:
        return cls_obj.getDeclaredConstructor(*resolved)
    return cls_obj.getDeclaredMethod(spec.method_name, *resolved)


def register_xposed(plugin: Any, attr_name: str, spec: XposedSpec) -> Any:
    """Зарегистрировать один декларативный Xposed-хук на устройстве.

    Безопасно: любая ошибка рефлексии логируется и не роняет загрузку
    плагина (рефлексия хрупка при обновлении приложения — pitfall #7).

    :param plugin: экземпляр плагина (источник ``hook_method`` и обработчика).
    :param attr_name: имя метода-обработчика на плагине.
    :param spec: спецификация хука.
    :returns: дескриптор для ``unhook_method`` либо ``None`` при неуспехе.
    """
    try:
        member = _resolve_member(spec)
        if member is None:
            _log(
                plugin,
                f"[catalib] Xposed: класс/метод не найден "
                f"({spec.class_fqn}.{spec.method_name or '<init>'}) — хук пропущен",
            )
            return None
        handler = getattr(plugin, attr_name)
        bridge = _make_bridge(handler, spec.phase, spec.filters)
        return plugin.hook_method(member, bridge, priority=spec.priority)
    except Exception as exc:  # рефлексия/SDK хрупки — не валим on_plugin_load
        _log(plugin, f"[catalib] Xposed: ошибка регистрации {spec.class_fqn}: {exc}")
        return None


def unregister_xposed(plugin: Any, handle: Any) -> None:
    """Снять один Xposed-хук, не роняя выгрузку при ошибке."""
    try:
        plugin.unhook_method(handle)
    except Exception as exc:
        _log(plugin, f"[catalib] Xposed: ошибка снятия хука: {exc}")
