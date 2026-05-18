"""Обёртки SDK ``extera_utils.classes`` — управляемый class proxy.

На устройстве **полностью** ре-экспортируется настоящий DSL exteraGram
(подклассы Java, переопределения, перегрузки, поля, конструкторы, MVEL,
``J``/``PyObj``) — он работает в полном объёме. Вне приложения —
функциональные офлайн-заглушки: декларации классов-проксей импортируются и
инстанцируются, ``jfield`` ведёт себя как атрибут со значением по
умолчанию, отрабатывают ``@jpreconstructor``/``__init__``/``@jconstructor``,
``J``/``PyObj`` проксируют Python-объект. Это честная граница офлайн-режима
(Java-родитель недоступен без устройства); на устройстве всегда
работает настоящий SDK.

Импорт делается одним блоком: ``extera_utils.classes`` — цельный API,
присутствует на устройстве полностью либо отсутствует офлайн целиком.
Зависит только от стандартной библиотеки и SDK.
"""

from __future__ import annotations

from typing import Any

try:  # pragma: no cover - ветка выполняется только на устройстве
    from extera_utils.classes import (
        Base,
        ClassHelper,
        J,
        JavaHelper,
        PyObj,
        java_subclass,
        jclassbuilder,
        jconstructor,
        jfield,
        jgetmethod,
        jmethod,
        jMVELmethod,
        jMVELoverride,
        joverload,
        joverride,
        jpreconstructor,
        jsetmethod,
    )
except Exception:  # pragma: no cover - ветка для обычного Python
    _JCTOR = "__catalib_jconstructor__"
    _JPRECTOR = "__catalib_jpreconstructor__"

    def _mark(attr: str, value: Any = True):
        """Вернуть декоратор, помечающий функцию атрибутом ``attr``."""

        def decorator(func: Any) -> Any:
            setattr(func, attr, value)
            return func

        return decorator

    def java_subclass(*bases: Any, **kwargs: Any):
        """Офлайн: фиксирует базовый Java-класс/интерфейсы, класс не меняет."""

        def decorator(cls: type) -> type:
            cls.__catalib_java_bases__ = bases
            cls.__catalib_java_kwargs__ = kwargs
            return cls

        return decorator

    def joverride(java_method_name: str | None = None):
        """Офлайн: пометить метод как переопределение Java-метода."""
        return _mark("__catalib_joverride__", java_method_name or True)

    def joverload(java_method_name: str, arg_types: list[Any]):
        """Офлайн: пометить метод как конкретную перегрузку."""
        return _mark("__catalib_joverload__", (java_method_name, tuple(arg_types)))

    def jmethod(
        java_method_name: str | None = None,
        return_type: str | None = None,
        arg_types: list[Any] | None = None,
    ):
        """Офлайн: пометить добавляемый в Java-класс метод."""
        return _mark(
            "__catalib_jmethod__",
            (java_method_name, return_type, tuple(arg_types or ())),
        )

    def jconstructor(arg_types: list[Any]):
        """Офлайн: пометить метод как пост-конструктор."""
        return _mark(_JCTOR, tuple(arg_types))

    def jpreconstructor(arg_types: list[Any]):
        """Офлайн: пометить classmethod как пред-конструктор."""
        return _mark(_JPRECTOR, tuple(arg_types))

    def jclassbuilder(*args: Any, **kwargs: Any):
        """Офлайн: декоратор кастомизации класса, функцию не меняет."""

        def decorator(func: Any) -> Any:
            func.__catalib_jclassbuilder__ = True
            return func

        return decorator

    class _MVELCallable:
        """Офлайн-плейсхолдер MVEL-метода/переопределения.

        Как атрибут класса доступен и вызываем; офлайн возвращает ``None``
        (тело на MVEL исполняется только на устройстве).
        """

        def __init__(self, kind: str, spec: dict[str, Any]) -> None:
            self.kind = kind
            self.spec = spec

        def __get__(self, obj: Any, owner: Any = None) -> Any:
            return self

        def __call__(self, *args: Any, **kwargs: Any) -> Any:
            return None

    def jMVELmethod(
        return_type: str | None = None,
        arguments: list[tuple[str, str]] | None = None,
        code: str = "",
    ) -> _MVELCallable:
        """Офлайн-плейсхолдер добавляемого MVEL-метода."""
        return _MVELCallable(
            "method",
            {"return_type": return_type, "arguments": arguments or [], "code": code},
        )

    def jMVELoverride(
        arguments: list[tuple[str, str]] | None = None, code: str = ""
    ) -> _MVELCallable:
        """Офлайн-плейсхолдер MVEL-переопределения."""
        return _MVELCallable("override", {"arguments": arguments or [], "code": code})

    class _JFieldMethod:
        """Маркер getter/setter, передаваемый в ``jfield(methods=[...])``."""

        def __init__(self, kind: str, java_name: str) -> None:
            self.kind = kind
            self.java_name = java_name

    def jgetmethod(java_method_name: str) -> _JFieldMethod:
        """Офлайн-маркер Java-getter'а поля."""
        return _JFieldMethod("get", java_method_name)

    def jsetmethod(java_method_name: str) -> _JFieldMethod:
        """Офлайн-маркер Java-setter'а поля."""
        return _JFieldMethod("set", java_method_name)

    class jfield:
        """Офлайн-дескриптор Java-поля: атрибут со значением по умолчанию.

        Хранит значение по экземпляру; читается/пишется как обычный
        атрибут (``self.counter += 1``). ``methods`` (getter/setter)
        офлайн принимается, но не нужен (Java-аксессоры — device-side).
        """

        def __init__(
            self,
            java_type: str,
            default: Any = None,
            methods: list[_JFieldMethod] | None = None,
        ) -> None:
            self.java_type = java_type
            self.default = default
            self.methods = methods or []
            self._name = "_catalib_jfield"

        def __set_name__(self, owner: type, name: str) -> None:
            self._name = f"_catalib_jfield_{name}"

        def __get__(self, obj: Any, owner: type | None = None) -> Any:
            if obj is None:
                return self
            return getattr(obj, self._name, self.default)

        def __set__(self, obj: Any, value: Any) -> None:
            object.__setattr__(obj, self._name, value)

    class Base:
        """Офлайн-база управляемого Java-подкласса.

        Поддерживает порядок инициализации без устройства:
        ``@jpreconstructor`` → ``__init__`` → ``@jconstructor`` →
        ``on_post_init``. Атрибуты ``java``/``this`` офлайн — ``None``.
        """

        java: Any = None
        this: Any = None

        @classmethod
        def bind(cls, *bases: Any) -> type:
            """Офлайн: фиксирует Java-базу/интерфейсы, возвращает класс."""
            cls.__catalib_java_bases__ = bases
            return cls

        @classmethod
        def java_class(cls) -> Any:
            """Сгенерированный Java-класс (офлайн — ``None``)."""
            return None

        @classmethod
        def _find_marked(cls, attr: str) -> Any:
            for name in dir(cls):
                member = getattr(cls, name, None)
                if callable(member) and hasattr(member, attr):
                    return name
            return None

        @classmethod
        def new_instance(cls, *args: Any, init_args: list[Any] | None = None) -> Base:
            """Создать Python-peer (офлайн, без Java).

            Повторяет порядок SDK: ``@jpreconstructor`` (может заменить
            аргументы) → ``__init__`` → ``@jconstructor`` →
            ``on_post_init``.
            """
            ctor_args = list(args)
            pre_name = cls._find_marked(_JPRECTOR)
            if pre_name is not None:
                # Сигнатура pre-конструктора — (cls, ...): офлайн декоратор
                # не оборачивает в classmethod, поэтому cls передаём явно.
                replaced = getattr(cls, pre_name)(cls, *ctor_args)
                if isinstance(replaced, list | tuple):
                    ctor_args = list(replaced)
                elif replaced is not None:
                    ctor_args = [replaced]
            instance = object.__new__(cls)
            instance.java = None
            instance.this = None
            init_with = init_args if init_args is not None else ctor_args
            # Если подкласс не определил собственный __init__, не передаём
            # аргументы в object.__init__ (иначе TypeError) — частый случай
            # из документации (subclass без __init__).
            if cls.__init__ is object.__init__:
                instance.__init__()
            else:
                instance.__init__(*init_with)
            ctor_name = cls._find_marked(_JCTOR)
            if ctor_name is not None:
                getattr(instance, ctor_name)(*ctor_args)
            post = getattr(instance, "on_post_init", None)
            if callable(post):
                post()
            return instance

        @classmethod
        def new_java_instance(cls, *args: Any) -> Any:
            """Сырой Java-объект (офлайн — ``None``)."""
            return None

        @classmethod
        def from_java(cls, java_instance: Any) -> Base:
            """Восстановить Python-peer из Java-объекта (офлайн — пустой)."""
            instance = object.__new__(cls)
            instance.java = java_instance
            instance.this = java_instance
            return instance

    class _JWrapper:
        """Офлайн-обёртка ``J``/``JavaHelper``/``ClassHelper``.

        Прозрачно проксирует чтение/запись атрибутов и вызовы методов на
        обёрнутый объект. Переключатели режимов (``JAccessAll`` и пр.) —
        неизменяемые: возвращают обёртку того же объекта.
        """

        def __init__(self, target: Any) -> None:
            object.__setattr__(self, "_target", target)

        def _same(self) -> _JWrapper:
            return self

        # Переключатели режимов (поведение SDK офлайн не меняет).
        JAccessAll = property(_same)
        JNotAccessAll = property(_same)
        JUseGetterAndSetter = property(_same)
        JNotUseGetterAndSetter = property(_same)
        JIgnoreResult = property(_same)
        JNotIgnoreResult = property(_same)

        def __getattr__(self, name: str) -> Any:
            return getattr(object.__getattribute__(self, "_target"), name)

        def __setattr__(self, name: str, value: Any) -> None:
            setattr(object.__getattribute__(self, "_target"), name, value)

        def __call__(self, *args: Any, **kwargs: Any) -> Any:
            return object.__getattribute__(self, "_target")(*args, **kwargs)

    def J(java_object: Any) -> _JWrapper:
        """Офлайн-обёртка над Python-объектом (passthrough)."""
        return _JWrapper(java_object)

    JavaHelper = J
    ClassHelper = J

    class PyObj:
        """Офлайн ``PyObj``: переносит Python-объект через Java-границу."""

        def __init__(self, value: Any) -> None:
            self.value = value

        @staticmethod
        def create(python_object: Any) -> PyObj:
            """Обернуть произвольный Python-объект."""
            return PyObj(python_object)

        def get(self) -> Any:
            """Вернуть исходный Python-объект."""
            return self.value


__all__ = [
    "Base",
    "ClassHelper",
    "J",
    "JavaHelper",
    "PyObj",
    "jMVELmethod",
    "jMVELoverride",
    "java_subclass",
    "jclassbuilder",
    "jconstructor",
    "jfield",
    "jgetmethod",
    "jmethod",
    "joverload",
    "joverride",
    "jpreconstructor",
    "jsetmethod",
]
