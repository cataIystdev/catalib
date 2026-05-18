"""Обёртка над ``adb`` для проброса порта dev server.

Прямой ``adb push`` в приватный каталог плагинов без root запрещён, поэтому
``adb`` используется только для ``forward`` порта dev server (см. ADR-0004).
Команды собираются списком аргументов — инъекции через shell исключены.
"""

from __future__ import annotations

import contextlib
import shutil
import subprocess

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
    """Выполнить команду и вернуть stdout; при ошибке поднять AdbError."""
    try:
        result = subprocess.run(args, capture_output=True, text=True, check=True)
    except FileNotFoundError as exc:
        raise AdbError("adb не найден в PATH") from exc
    except subprocess.CalledProcessError as exc:
        raise AdbError(
            f"команда adb завершилась с ошибкой: {' '.join(args)}\n{exc.stderr.strip()}"
        ) from exc
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


def logcat(lines: int = 100, serial: str | None = None, *, clear: bool = False) -> str:
    """Прочитать последние ``lines`` строк logcat устройства.

    Команда совпадает с инструментом MCP ``adb_get_logs`` (единое
    поведение): ``logcat -d -t <lines>``; при ``clear`` сначала
    ``logcat -c`` (ошибка очистки не фатальна).

    :param lines: сколько последних строк вернуть.
    :param serial: серийный номер устройства (если их несколько).
    :param clear: очистить буфер логов перед чтением.
    :raises AdbError: если ``adb`` недоступен или устройство не отвечает.
    """
    if clear:
        with contextlib.suppress(AdbError):
            _run([*_adb_base(serial), "logcat", "-c"])
    return _run([*_adb_base(serial), "logcat", "-d", "-t", str(lines)])
