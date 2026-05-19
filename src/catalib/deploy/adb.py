"""Обёртка над ``adb`` для проброса порта dev server.

Прямой ``adb push`` в приватный каталог плагинов без root запрещён, поэтому
``adb`` используется только для ``forward`` порта dev server (см. ADR-0004).
Команды собираются списком аргументов — инъекции через shell исключены.
"""

from __future__ import annotations

import contextlib
import shutil
import subprocess

from catalib.platforms import should_use_adb

#: Порт dev server exteraGram по умолчанию.
DEV_SERVER_PORT = 42690


class AdbError(RuntimeError):
    """Ошибка вызова ``adb`` или отсутствия устройства."""


def _adb_base(serial: str | None) -> list[str]:
    """Базовая команда ``adb`` с необязательным выбором устройства."""
    if shutil.which("adb") is None:
        raise AdbError("adb не найден в PATH; установите Android platform-tools")
    base = ["adb"]
    if serial:
        base += ["-s", serial]
    return base


def _run(args: list[str]) -> str:
    """Выполнить команду и вернуть stdout; при ошибке поднять AdbError.

    Сообщения об ошибке используют имя самой команды (``args[0]``),
    поэтому функция годится и для ``adb``, и для прямого ``logcat`` на
    устройстве. ``OSError`` (например, запрет ``subprocess`` в песочнице
    Pydroid) тоже оборачивается в :class:`AdbError` — инструмент должен
    деградировать понятным сообщением, а не падать (см. ADR-0011).
    """
    tool = args[0]
    try:
        result = subprocess.run(args, capture_output=True, text=True, check=True)
    except FileNotFoundError as exc:
        raise AdbError(f"{tool} не найден в PATH") from exc
    except subprocess.CalledProcessError as exc:
        raise AdbError(
            f"команда {tool} завершилась с ошибкой: {' '.join(args)}\n{exc.stderr.strip()}"
        ) from exc
    except OSError as exc:
        raise AdbError(f"{tool} недоступен: {exc}") from exc
    return result.stdout.strip()


def list_devices() -> list[str]:
    """Вернуть серийные номера подключённых устройств в состоянии ``device``."""
    out = _run([*_adb_base(None), "devices"])
    serials = []
    for line in out.splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "device":
            serials.append(parts[0])
    return serials


def forward_dev_server(local_port: int, serial: str | None = None) -> None:
    """Пробросить ``tcp:local_port`` на ``tcp:DEV_SERVER_PORT`` устройства."""
    _run(
        [
            *_adb_base(serial),
            "forward",
            f"tcp:{local_port}",
            f"tcp:{DEV_SERVER_PORT}",
        ]
    )


def remove_forward(local_port: int, serial: str | None = None) -> None:
    """Снять ранее установленный проброс порта (ошибки игнорируются)."""
    with contextlib.suppress(AdbError):
        _run([*_adb_base(serial), "forward", "--remove", f"tcp:{local_port}"])


def _logcat_prefix(serial: str | None, use_adb: bool | None) -> list[str]:
    """Базовая команда logcat: ``adb [-s ..] logcat`` либо прямой ``logcat``.

    На самом устройстве (Android) ``adb`` нет — системный ``logcat``
    вызывается напрямую (см. ADR-0011). На ПК — через ``adb``.
    """
    if should_use_adb(use_adb):
        return [*_adb_base(serial), "logcat"]
    return ["logcat"]


def logcat(
    lines: int = 100,
    serial: str | None = None,
    *,
    clear: bool = False,
    use_adb: bool | None = None,
) -> str:
    """Прочитать последние ``lines`` строк logcat.

    Команда совпадает с инструментом MCP ``adb_get_logs`` (единое
    поведение): ``logcat -d -t <lines>``; при ``clear`` сначала
    ``logcat -c`` (ошибка очистки не фатальна). На ПК — через ``adb``,
    на устройстве — системный ``logcat`` напрямую.

    :param lines: сколько последних строк вернуть.
    :param serial: серийный номер устройства (только для пути с ``adb``).
    :param clear: очистить буфер логов перед чтением.
    :param use_adb: ``True``/``False`` явно; ``None`` — авто (на Android
        напрямую без ``adb``).
    :raises AdbError: если ``adb``/``logcat`` недоступен (в т. ч. запрет
        ``subprocess``) или команда завершилась ошибкой.
    """
    prefix = _logcat_prefix(serial, use_adb)
    if clear:
        with contextlib.suppress(AdbError):
            _run([*prefix, "-c"])
    return _run([*prefix, "-d", "-t", str(lines)])
