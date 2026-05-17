"""Встраиваемый загрузчик модульного плагина.

Исходник этого модуля целиком встраивается в собранный ``<plugin_id>.py``.
Он не зависит ни от чего, кроме стандартной библиотеки, и не порождает
процессы (подпроцессы в Chaquopy недоступны).

Идея: собранный файл импортируется exteraGram как модуль ``<plugin_id>``.
Этот модуль объявляется пакетом, а все исходные модули плагина
регистрируются как его подмодули ``<plugin_id>.<имя>`` через собственный
finder в ``sys.meta_path``. Имена уникальны, так как ``<plugin_id>``
уникален в exteraGram. Каждый модуль компилируется с собственным origin и
регистрируется в ``linecache`` — трейсбеки указывают на исходные файлы.
"""

import importlib
import importlib.util
import linecache
import sys

#: Ключ в ``sources``: значение — кортеж ``(исходник, признак_пакета, origin)``.
#: Ключи — полные рантайм-имена модулей (``<plugin_id>`` и ``<plugin_id>.*``).


class _CatalibLoader:
    """Загрузчик одного встроенного модуля из строки-исходника."""

    def __init__(self, plugin_id, source, origin, is_package):
        self._catalib_plugin = plugin_id
        self._source = source
        self._origin = origin
        self._is_package = is_package

    def create_module(self, spec):
        """Использовать стандартное создание модуля."""
        return None

    def exec_module(self, module):
        """Зарегистрировать исходник в linecache и исполнить модуль."""
        linecache.cache[self._origin] = (
            len(self._source),
            None,
            self._source.splitlines(keepends=True),
            self._origin,
        )
        code = compile(self._source, self._origin, "exec")
        exec(code, module.__dict__)


class _CatalibFinder:
    """Finder в ``sys.meta_path``, отдающий подмодули конкретного плагина."""

    def __init__(self, plugin_id, sources):
        self._catalib_plugin = plugin_id
        self._sources = sources

    def find_spec(self, fullname, path=None, target=None):
        """Вернуть spec для встроенного подмодуля плагина либо ``None``."""
        entry = self._sources.get(fullname)
        if entry is None or fullname == self._catalib_plugin:
            return None
        source, is_package, origin = entry
        loader = _CatalibLoader(self._catalib_plugin, source, origin, is_package)
        return importlib.util.spec_from_loader(
            fullname, loader, origin=origin, is_package=is_package
        )


def _find_plugin_class(namespace):
    """Найти в пространстве имён класс плагина (подкласс BasePlugin).

    Сначала пытается строгую проверку через ``base_plugin.BasePlugin``.
    Если SDK недоступен (офлайн-тесты), опирается на имена базовых классов.
    """
    base_cls = None
    try:
        import base_plugin

        base_cls = base_plugin.BasePlugin
    except Exception:
        base_cls = None

    candidates = []
    for value in namespace.values():
        if not isinstance(value, type):
            continue
        if base_cls is not None:
            if issubclass(value, base_cls) and value is not base_cls:
                candidates.append(value)
        else:
            base_names = {klass.__name__ for klass in value.__mro__[1:]}
            if base_names & {"BasePlugin", "CatalibPlugin"}:
                candidates.append(value)
    for value in candidates:
        if getattr(value, "__catalib_plugin__", False):
            return value
    return candidates[0] if candidates else None


def catalib_install(module_name, module_globals, sources, entry_fullname):
    """Активировать встроенный загрузчик плагина.

    :param module_name: имя верхнего модуля (``<plugin_id>``).
    :param module_globals: ``globals()`` собранного модуля.
    :param sources: отображение «полное имя -> (исходник, пакет?, origin)».
    :param entry_fullname: полное имя модуля точки входа.
    """
    # Снять прежние finder'ы и подмодули этого плагина (безопасный reload).
    sys.meta_path[:] = [
        f for f in sys.meta_path if getattr(f, "_catalib_plugin", None) != module_name
    ]
    prefix = module_name + "."
    for name in [n for n in sys.modules if n.startswith(prefix)]:
        del sys.modules[name]

    sys.meta_path.insert(0, _CatalibFinder(module_name, sources))

    # Метаданные плагина задаются литералом ``__name__ = "<display>"``, что
    # перетирает реальное имя модуля и ломает относительные импорты.
    # Восстанавливаем идентичность модуля и делаем его пакетом.
    module_globals["__name__"] = module_name
    module_globals["__package__"] = module_name
    module_globals.setdefault("__path__", [])
    # Согласовать __spec__ с тем, что модуль теперь пакет, иначе Python
    # предупреждает о расхождении __package__ и __spec__.parent.
    spec = module_globals.get("__spec__")
    if spec is not None and getattr(spec, "submodule_search_locations", None) is None:
        spec.submodule_search_locations = []

    # Тело корневого модуля (src/__init__.py) исполнить в этом же модуле.
    root = sources.get(module_name)
    if root is not None:
        source, _is_package, origin = root
        linecache.cache[origin] = (
            len(source),
            None,
            source.splitlines(keepends=True),
            origin,
        )
        exec(compile(source, origin, "exec"), module_globals)

    # Импортировать точку входа и поднять класс плагина на верхний уровень.
    if entry_fullname != module_name:
        entry_module = importlib.import_module(entry_fullname)
        plugin_class = _find_plugin_class(vars(entry_module))
        if plugin_class is not None and plugin_class.__name__ not in module_globals:
            module_globals[plugin_class.__name__] = plugin_class
