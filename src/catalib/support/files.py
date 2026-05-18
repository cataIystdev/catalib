"""Обёртки модуля SDK ``file_utils``.

На устройстве вызываются настоящие функции exteraGram; вне приложения —
**полноценные** реализации на стандартной библиотеке (реальная работа с
файловой системой во временных каталогах). Это не заглушки-пустышки:
офлайн ``write_file``/``read_file``/``list_dir``/``delete_file``/
``ensure_dir_exists`` действительно работают, что и даёт офлайн-тестируемость
плагинов; на устройстве всегда работает настоящий SDK.

Контракты повторяют документацию file-utils: ``write_file`` не создаёт
родительские каталоги; ``read_file`` возвращает ``None`` при ошибке;
``delete_file`` — ``bool``. Зависит только от стандартной библиотеки и SDK.
"""

from __future__ import annotations

import os
import tempfile

# ``get_plugins_dir`` офлайн возвращает сам temp-каталог (прежний контракт
# :func:`catalib.support.sdk.get_plugins_dir` сохранён); остальные getter'ы —
# различимые подпапки во временном каталоге.


def _device_dir(getter_name: str) -> str | None:
    """Вернуть путь от настоящего ``file_utils`` либо ``None`` офлайн."""
    try:  # pragma: no cover - на устройстве
        import file_utils

        return getattr(file_utils, getter_name)()
    except Exception:
        return None


def get_plugins_dir() -> str:
    """Каталог плагинов; офлайн — системный временный каталог."""
    return _device_dir("get_plugins_dir") or tempfile.gettempdir()


def get_cache_dir() -> str:
    """Кеш приложения; офлайн — подпапка во временном каталоге."""
    return _device_dir("get_cache_dir") or os.path.join(
        tempfile.gettempdir(), "catalib_offline_cache"
    )


def get_files_dir() -> str:
    """Файловый каталог приложения; офлайн — подпапка temp."""
    return _device_dir("get_files_dir") or os.path.join(
        tempfile.gettempdir(), "catalib_offline_files"
    )


def get_images_dir() -> str:
    """Каталог изображений; офлайн — подпапка temp."""
    return _device_dir("get_images_dir") or os.path.join(
        tempfile.gettempdir(), "catalib_offline_images"
    )


def get_videos_dir() -> str:
    """Каталог видео; офлайн — подпапка temp."""
    return _device_dir("get_videos_dir") or os.path.join(
        tempfile.gettempdir(), "catalib_offline_videos"
    )


def get_audios_dir() -> str:
    """Каталог аудио; офлайн — подпапка temp."""
    return _device_dir("get_audios_dir") or os.path.join(
        tempfile.gettempdir(), "catalib_offline_audios"
    )


def get_documents_dir() -> str:
    """Каталог документов; офлайн — подпапка temp."""
    return _device_dir("get_documents_dir") or os.path.join(
        tempfile.gettempdir(), "catalib_offline_documents"
    )


def ensure_dir_exists(path: str) -> None:
    """Создать каталог (с родителями), если его ещё нет.

    :param path: путь каталога.
    """
    try:  # pragma: no cover - на устройстве
        from file_utils import ensure_dir_exists as _ensure

        _ensure(path)
        return
    except Exception:
        os.makedirs(path, exist_ok=True)


def list_dir(
    path: str,
    recursive: bool = False,
    include_files: bool = True,
    include_dirs: bool = False,
    extensions: list[str] | None = None,
) -> list[str]:
    """Перечислить содержимое каталога.

    :param path: каталог.
    :param recursive: обходить вложенные каталоги.
    :param include_files: включать файлы.
    :param include_dirs: включать каталоги.
    :param extensions: фильтр по суффиксам (например ``[".json", ".txt"]``).
    :returns: список абсолютных путей.
    """
    try:  # pragma: no cover - на устройстве
        from file_utils import list_dir as _list

        return _list(path, recursive, include_files, include_dirs, extensions)
    except Exception:
        pass
    result: list[str] = []
    if not os.path.isdir(path):
        return result

    def _match_ext(name: str) -> bool:
        if not extensions:
            return True
        return any(name.endswith(ext) for ext in extensions)

    if recursive:
        for root, dirs, files in os.walk(path):
            if include_dirs:
                result.extend(os.path.join(root, d) for d in dirs)
            if include_files:
                result.extend(
                    os.path.join(root, f) for f in files if _match_ext(f)
                )
    else:
        for entry in os.scandir(path):
            if entry.is_dir():
                if include_dirs:
                    result.append(entry.path)
            elif include_files and _match_ext(entry.name):
                result.append(entry.path)
    return result


def write_file(path: str, content: str) -> None:
    """Записать строку в файл (перезапись).

    Родительские каталоги не создаются (как в SDK) — отсутствие каталога
    приводит к ошибке; используйте :func:`ensure_dir_exists` заранее.

    :param path: путь к файлу.
    :param content: содержимое.
    """
    try:  # pragma: no cover - на устройстве
        from file_utils import write_file as _write

        _write(path, content)
        return
    except Exception:
        pass
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(content)


def read_file(path: str) -> str | None:
    """Прочитать файл целиком.

    :param path: путь к файлу.
    :returns: содержимое или ``None`` при ошибке (как в SDK).
    """
    try:  # pragma: no cover - на устройстве
        from file_utils import read_file as _read

        return _read(path)
    except Exception:
        pass
    try:
        with open(path, encoding="utf-8") as handle:
            return handle.read()
    except Exception:
        return None


def delete_file(path: str) -> bool:
    """Удалить файл.

    :param path: путь к файлу.
    :returns: ``True`` при успешном удалении, иначе ``False``.
    """
    try:  # pragma: no cover - на устройстве
        from file_utils import delete_file as _delete

        return _delete(path)
    except Exception:
        pass
    try:
        os.remove(path)
        return True
    except Exception:
        return False


__all__ = [
    "delete_file",
    "ensure_dir_exists",
    "get_audios_dir",
    "get_cache_dir",
    "get_documents_dir",
    "get_files_dir",
    "get_images_dir",
    "get_plugins_dir",
    "get_videos_dir",
    "list_dir",
    "read_file",
    "write_file",
]
