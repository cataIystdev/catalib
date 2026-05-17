"""Зонд среды Chaquopy для проверки применимости механизма catalib.

Плагин read-only: только собирает диагностику и пишет её в JSON рядом с собой,
а также дублирует в логи. Никакие пользовательские данные не изменяются.

Проверяет ключевые гипотезы ADR-0002:

- можно ли зарегистрировать собственный ``MetaPathFinder`` в ``sys.meta_path``
  и импортировать через него синтетический модуль;
- работают ли пакеты и относительные импорты через такой finder;
- указывает ли трейсбек на исходный «файл» благодаря ``linecache``;
- каков ``sys.path``, идентичность модуля плагина, состав ``sys.modules``;
- доступен ли каталог плагина для записи.

Файл написан вручную, без ядра catalib, и собран в один модуль намеренно.
"""

import contextlib
import json
import linecache
import os
import sys
import traceback

__id__ = "catalib_probe"
__name__ = "Catalib Probe"
__description__ = "Read-only диагностика среды Chaquopy для catalib"
__author__ = "catalyst"
__version__ = "0.1.0"
__icon__ = "exteraPlugins/1"
__app_version__ = ">=12.5.1"
__sdk_version__ = ">=1.4.3.6"

try:
    from base_plugin import BasePlugin

    _SDK_AVAILABLE = True
except Exception:  # pragma: no cover - ветка для исполнения вне exteraGram
    _SDK_AVAILABLE = False

    class BasePlugin:
        """Заглушка базового класса для запуска вне exteraGram."""

        def log(self, message: str) -> None:
            print(message)


def _sdk_log(message: str) -> None:
    """Записать строку и в лог приложения, и в stdout.

    Chaquopy перенаправляет stdout в logcat, поэтому print гарантирует
    захват результата через ``adb logcat`` независимо от поведения SDK-лога.
    Подпроцессы в Chaquopy недоступны, поэтому здесь только безопасные вызовы.
    """
    with contextlib.suppress(Exception):
        from android_utils import log as _log

        _log(message)
    with contextlib.suppress(Exception):
        print(message, flush=True)


# Уникальный приватный префикс пространства имён, производный от идентификатора
# плагина. Именно так ядро catalib будет изолировать встроенные модули.
_PREFIX = "_catalib_probe_ns"


class _InMemoryLoader:
    """Загрузчик, исполняющий исходник модуля из строки в памяти.

    Регистрирует исходник в ``linecache`` под синтетическим путём, чтобы
    трейсбеки указывали на «файл», как это требуется ядру catalib.
    """

    def __init__(self, fullname: str, source: str, origin: str, is_package: bool):
        self._fullname = fullname
        self._source = source
        self._origin = origin
        self._is_package = is_package

    def create_module(self, spec):
        return None

    def exec_module(self, module) -> None:
        linecache.cache[self._origin] = (
            len(self._source),
            None,
            self._source.splitlines(keepends=True),
            self._origin,
        )
        code = compile(self._source, self._origin, "exec")
        exec(code, module.__dict__)


class _InMemoryFinder:
    """Finder для ``sys.meta_path``, отдающий заранее заданные модули."""

    def __init__(self, modules: dict):
        # modules: fullname -> (source, is_package)
        self._modules = modules

    def find_spec(self, fullname, path=None, target=None):
        if fullname not in self._modules:
            return None
        import importlib.util

        source, is_package = self._modules[fullname]
        origin = f"<catalib-probe:{fullname}>"
        loader = _InMemoryLoader(fullname, source, origin, is_package)
        spec = importlib.util.spec_from_loader(
            fullname, loader, origin=origin, is_package=is_package
        )
        return spec


def _run_diagnostics() -> dict:
    """Собрать диагностику среды и вернуть её словарём."""
    result: dict = {"steps": {}, "errors": {}}

    def record(step: str, value) -> None:
        result["steps"][step] = value

    def fail(step: str, exc: BaseException) -> None:
        result["errors"][step] = f"{type(exc).__name__}: {exc}"

    # Базовая идентификация среды. Подпроцессы в Chaquopy недоступны
    # (нативный креш в _posixsubprocess), поэтому platform.platform()
    # не используется: только безопасные источники без fork/exec.
    try:
        uname = None
        try:
            raw = os.uname()
            uname = {"sysname": raw.sysname, "release": raw.release, "machine": raw.machine}
        except Exception as uexc:
            uname = f"unavailable: {type(uexc).__name__}"
        record(
            "environment",
            {
                "python_version": sys.version,
                "sys_platform": sys.platform,
                "uname": uname,
                "executable": sys.executable,
                "sdk_available": _SDK_AVAILABLE,
            },
        )
    except Exception as exc:
        fail("environment", exc)

    # Идентичность модуля плагина.
    try:
        record(
            "module_identity",
            {
                "name": __name__,
                "file": globals().get("__file__"),
                "package": globals().get("__package__"),
                "in_sys_modules": __id__ in sys.modules,
                "self_module_file": getattr(sys.modules.get(__id__, None), "__file__", None),
            },
        )
    except Exception as exc:
        fail("module_identity", exc)

    # Состояние путей и хуков импорта.
    try:
        record(
            "import_state",
            {
                "sys_path": list(sys.path),
                "meta_path": [type(m).__name__ for m in sys.meta_path],
                "path_hooks": [getattr(h, "__name__", repr(h)) for h in sys.path_hooks],
                "related_modules": sorted(k for k in sys.modules if __id__ in k or _PREFIX in k),
            },
        )
    except Exception as exc:
        fail("import_state", exc)

    # Главная проверка: собственный finder в sys.meta_path, пакет с
    # относительным импортом и трейсбек, указывающий на синтетический файл.
    finder = None
    created = []
    try:
        import importlib

        pkg = f"{_PREFIX}_pkg"
        modules = {
            pkg: ("VALUE = 41\n", True),
            f"{pkg}.sub": (
                "from . import VALUE\n"
                "\n"
                "def compute():\n"
                "    return VALUE + 1\n"
                "\n"
                "def boom():\n"
                "    raise ValueError('synthetic failure')\n",
                False,
            ),
        }
        finder = _InMemoryFinder(modules)
        sys.meta_path.insert(0, finder)

        sub = importlib.import_module(f"{pkg}.sub")
        created = [pkg, f"{pkg}.sub"]

        relative_import_ok = sub.compute() == 42

        traceback_points_to_synthetic = False
        traceback_text = ""
        try:
            sub.boom()
        except ValueError:
            traceback_text = traceback.format_exc()
            traceback_points_to_synthetic = (
                f"<catalib-probe:{pkg}.sub>" in traceback_text
                and "raise ValueError('synthetic failure')" in traceback_text
            )

        record(
            "meta_path_mechanism",
            {
                "custom_finder_registered": finder in sys.meta_path,
                "synthetic_package_imported": created == [pkg, f"{pkg}.sub"],
                "relative_import_ok": relative_import_ok,
                "traceback_points_to_synthetic": traceback_points_to_synthetic,
                "traceback_excerpt": traceback_text.strip().splitlines()[-3:]
                if traceback_text
                else [],
            },
        )
    except Exception as exc:
        fail("meta_path_mechanism", exc)
    finally:
        try:
            if finder is not None and finder in sys.meta_path:
                sys.meta_path.remove(finder)
            for name in created:
                sys.modules.pop(name, None)
                linecache.cache.pop(f"<catalib-probe:{name}>", None)
        except Exception as exc:
            fail("meta_path_cleanup", exc)

    # Доступность каталогов и запись.
    try:
        from file_utils import get_files_dir, get_plugins_dir

        plugins_dir = get_plugins_dir()
        files_dir = get_files_dir()
    except Exception as exc:
        plugins_dir = None
        files_dir = None
        fail("dirs_import", exc)

    try:
        write_target = None
        write_ok = False
        if plugins_dir:
            data_dir = os.path.join(plugins_dir, "catalib_probe_data")
            os.makedirs(data_dir, exist_ok=True)
            probe_file = os.path.join(data_dir, "write_test.txt")
            with open(probe_file, "w", encoding="utf-8") as handle:
                handle.write("ok")
            with open(probe_file, encoding="utf-8") as handle:
                write_ok = handle.read() == "ok"
            os.remove(probe_file)
            os.rmdir(data_dir)
            write_target = data_dir
        record(
            "filesystem",
            {
                "plugins_dir": plugins_dir,
                "files_dir": files_dir,
                "write_dir": write_target,
                "write_ok": write_ok,
            },
        )
    except Exception as exc:
        fail("filesystem", exc)

    return result


def _emit(result: dict) -> str:
    """Записать результат во все доступные места и вернуть фактический путь.

    Каталог плагина приватен и недоступен через adb, поэтому результат
    дополнительно пишется в общее хранилище (``/sdcard``), откуда его можно
    забрать ``adb pull`` без root.
    """
    text = json.dumps(result, ensure_ascii=False, indent=2)
    written = []
    targets = [
        "/sdcard/catalib_probe_result.json",
        "/storage/emulated/0/catalib_probe_result.json",
        "/storage/emulated/0/Android/data/com.exteragram.messenger/files/catalib_probe_result.json",
    ]
    try:
        from file_utils import get_plugins_dir

        targets.insert(0, os.path.join(get_plugins_dir(), "catalib_probe_result.json"))
    except Exception as exc:
        _sdk_log(f"[catalib_probe] get_plugins_dir недоступен: {exc}")
    for target in targets:
        try:
            with open(target, "w", encoding="utf-8") as handle:
                handle.write(text)
            written.append(target)
        except Exception as exc:
            _sdk_log(f"[catalib_probe] не записать {target}: {exc}")
    _sdk_log("[catalib_probe] RESULT BEGIN")
    for line in text.splitlines():
        _sdk_log("[catalib_probe] " + line)
    _sdk_log("[catalib_probe] RESULT END")
    return ",".join(written)


class CatalibProbePlugin(BasePlugin):
    """Плагин-зонд: при загрузке собирает диагностику и публикует её."""

    def on_plugin_load(self) -> None:
        _sdk_log("[catalib_probe] ON_PLUGIN_LOAD START")
        try:
            result = _run_diagnostics()
            path = _emit(result)
            _sdk_log(f"[catalib_probe] диагностика записана: {path}")
        except Exception as exc:
            _sdk_log(f"[catalib_probe] фатальная ошибка зонда: {exc}")
            _sdk_log(traceback.format_exc())

    def on_plugin_unload(self) -> None:
        for name in list(sys.modules):
            if name.startswith(_PREFIX):
                sys.modules.pop(name, None)


# Диагностика запускается на уровне модуля: движок exteraGram исполняет тело
# модуля при каждом импорте через getModule(<plugin_id>) независимо от того,
# включён ли плагин и вызывается ли on_plugin_load. Любые сбои подавляются,
# чтобы импорт модуля не помечался движком как ошибочный.
with contextlib.suppress(Exception):
    _sdk_log("[catalib_probe] MODULE IMPORT START")
    _emit(_run_diagnostics())
    _sdk_log("[catalib_probe] MODULE IMPORT DONE")
