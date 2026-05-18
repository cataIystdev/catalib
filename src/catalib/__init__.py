"""catalib — инструмент сборки модульных плагинов exteraGram в один файл.

Пакет содержит две среды исполнения с жёсткой границей между ними:

- Среда инструмента (подпакеты ``cli``, ``manifest``, ``bundler``, ``deploy``,
  ``scaffold``) — исполняется на машине разработчика.
- Встраиваемая среда (подпакеты ``runtime``, ``support``) — её исходники
  попадают внутрь собранного плагина и исполняются под Chaquopy на устройстве,
  поэтому зависят только от стандартной библиотеки и SDK exteraGram.

Здесь же объявлена :func:`check_for_updates` — безопасная проверка наличия
более новой версии catalib на PyPI. Все её зависимости (``urllib``,
``json`` и т. п.) импортируются **лениво внутри функции**: при обычном
``import catalib`` (в т. ч. в вендоренном виде внутри плагина на
устройстве) никаких сетевых запросов и тяжёлых импортов не происходит.
Вызывается из CLI; никогда не роняет команду.
"""

from __future__ import annotations

__all__ = ["__version__", "check_for_updates"]

#: Версия пакета. Единый источник истины — синхронизирована с ``pyproject.toml``.
__version__ = "0.3.2"

#: Имя пакета на PyPI и переменная окружения для отключения проверки.
_PYPI_JSON_URL = "https://pypi.org/pypi/catalib/json"
_OPT_OUT_ENV = "CATALIB_NO_UPDATE_CHECK"
#: Срок жизни кеша последней проверки, секунд (сутки).
_CACHE_TTL_SECONDS = 24 * 60 * 60


def _parse_version(value: str) -> tuple[int, ...]:
    """Разобрать строку версии ``X.Y.Z`` в кортеж чисел для сравнения.

    Нечисловые/пред-релизные части отбрасываются с первого нечислового
    сегмента (грубое, но безопасное сравнение SemVer без внешних
    зависимостей: ложного «доступно обновление» не даёт).
    """
    parts: list[int] = []
    for chunk in value.strip().split("."):
        if chunk.isdigit():
            parts.append(int(chunk))
        else:
            break
    return tuple(parts)


def _is_newer(latest: str, current: str) -> bool:
    """``True``, если ``latest`` строго новее ``current``."""
    lp, cp = _parse_version(latest), _parse_version(current)
    if not lp or not cp:
        return False
    return lp > cp


def _cache_path() -> str:
    """Путь к файлу кеша проверки обновлений (в каталоге кеша пользователя)."""
    import os

    base = os.environ.get("XDG_CACHE_HOME") or os.path.join(
        os.path.expanduser("~"), ".cache"
    )
    return os.path.join(base, "catalib", "update-check.json")


def _read_cache(now: float) -> str | None:
    """Вернуть закешированную последнюю версию, если кеш свежий, иначе ``None``."""
    import json

    try:
        with open(_cache_path(), encoding="utf-8") as handle:
            data = json.load(handle)
        if now - float(data["ts"]) < _CACHE_TTL_SECONDS:
            latest = data.get("latest")
            return latest if isinstance(latest, str) else None
    except Exception:
        return None
    return None


def _write_cache(now: float, latest: str) -> None:
    """Сохранить результат проверки (без падения при ошибке ФС)."""
    import json
    import os

    try:
        path = _cache_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump({"ts": now, "latest": latest}, handle)
    except Exception:
        pass


def _fetch_latest_version(timeout: float) -> str | None:
    """Запросить последнюю версию catalib с PyPI (или ``None`` при ошибке)."""
    import json
    import urllib.request

    try:
        with urllib.request.urlopen(_PYPI_JSON_URL, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        version = payload["info"]["version"]
        return version if isinstance(version, str) else None
    except Exception:
        return None


def check_for_updates(timeout: float = 2.5) -> str | None:
    """Проверить, есть ли на PyPI более новая версия catalib.

    Полностью безопасна: при отключении, любой ошибке сети, таймауте или
    проблеме с кешем возвращает ``None`` и ничего не печатает. Сетевой
    запрос делается не чаще раза в сутки (кеш
    ``~/.cache/catalib/update-check.json``). Отключается переменной
    окружения ``CATALIB_NO_UPDATE_CHECK=1``. Не вызывается при импорте
    пакета — только из CLI.

    :param timeout: таймаут HTTP-запроса к PyPI в секундах.
    :returns: строка более новой версии (например ``"0.4.0"``) либо
        ``None``, если обновления нет или проверку выполнить не удалось.
    """
    import os
    import time

    if os.environ.get(_OPT_OUT_ENV, "").strip() not in ("", "0", "false", "False"):
        return None

    now = time.time()
    latest = _read_cache(now)
    if latest is None:
        latest = _fetch_latest_version(timeout)
        if latest is None:
            return None
        _write_cache(now, latest)

    return latest if _is_newer(latest, __version__) else None
