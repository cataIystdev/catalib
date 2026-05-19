"""Префлайт-диагностика окружения разработки плагинов.

``catalib doctor`` проверяет, что окружение готово к сборке и деплою:
версия Python, среда (ПК или Android: Termux/Pydroid), доступность dev
server, валидность ``catalib.toml``. Каждая проверка возвращает
:class:`Check` со статусом ``ok``/``warn``/``fail``.

На ПК dev server проверяется через временный ``adb forward`` (плюс
проверки ``adb``/устройства). На самом устройстве (Android) ``adb`` не
нужен — dev server проверяется напрямую (``127.0.0.1:<port>``), а вместо
``adb``/устройства печатается среда. См. ADR-0011.

Диагностика никогда не бросает исключений и не имеет побочных эффектов
сверх временного ``adb forward`` (который сразу снимается) — это
инструмент проверки, а не сборка. Отсутствие ``adb``/устройства/dev
server — это ``warn`` (нужно только для деплоя), а не ``fail``; ``fail``
зарезервирован за тем, что точно сломает сборку (старый Python, битый
манифест).
"""

from __future__ import annotations

import shutil
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from catalib import __version__
from catalib.deploy.adb import AdbError, forward_dev_server, list_devices, remove_forward
from catalib.deploy.devserver import DevServerClient, DevServerError
from catalib.manifest.loader import MANIFEST_FILENAME, load_manifest
from catalib.manifest.model import ManifestError
from catalib.platforms import PYDROID, android_flavor, describe_environment, is_android

#: Проверка пройдена.
OK = "ok"
#: Не критично — нужно только для части сценариев (обычно деплой).
WARN = "warn"
#: Критично — сборка точно не получится, пока не исправить.
FAIL = "fail"

#: Минимальная версия Python (совпадает с ``requires-python`` catalib).
MIN_PYTHON = (3, 11)


@dataclass(frozen=True, slots=True)
class Check:
    """Результат одной проверки окружения.

    :param name: краткое имя проверки (для вывода).
    :param status: один из :data:`OK`, :data:`WARN`, :data:`FAIL`.
    :param detail: что обнаружено.
    :param hint: как починить (имеет смысл при ``warn``/``fail``).
    """

    name: str
    status: str
    detail: str
    hint: str = ""


def _check_python() -> Check:
    """Версия интерпретатора разработчика не ниже :data:`MIN_PYTHON`."""
    info = sys.version_info
    current = f"{info.major}.{info.minor}.{info.micro}"
    if (info.major, info.minor) >= MIN_PYTHON:
        return Check("Python", OK, f"{current} (>= 3.11)")
    return Check(
        "Python",
        FAIL,
        f"{current} — catalib требует Python >= 3.11",
        hint="установите Python 3.11+ и пересоздайте виртуальное окружение",
    )


def _check_catalib() -> Check:
    """Версия самого catalib (всегда информационно ``ok``)."""
    return Check("catalib", OK, f"версия {__version__}")


def _check_environment() -> Check:
    """Среда запуска (ПК или Android: Termux/Pydroid). Информационно ``ok``."""
    detail = describe_environment()
    if android_flavor() == PYDROID:
        # Pydroid — песочница: subprocess может быть урезан, поэтому
        # диагностика устройства/логов на нём может деградировать.
        detail += " — subprocess может быть урезан (logs/диагностика)"
    return Check("Среда", OK, detail)


def _check_devserver_direct(port: int, devserver_client: DevServerClient | None) -> Check:
    """Прямое подключение к dev server на устройстве (без ``adb``).

    На Android процесс уже на устройстве: dev server слушает
    ``127.0.0.1:<port>``, ``adb forward`` не нужен (см. ADR-0011).
    """
    client = devserver_client or DevServerClient(port=port, timeout=5.0)
    owns = devserver_client is None
    try:
        client.connect()
        answered = client.ping()
    except DevServerError as exc:
        return Check(
            "Dev server",
            WARN,
            f"недоступен напрямую: {exc}",
            hint="запустите exteraGram и включите режим разработчика",
        )
    finally:
        if owns:
            client.close()
    if answered:
        return Check("Dev server", OK, f"доступен напрямую на 127.0.0.1:{port}")
    return Check("Dev server", WARN, "не ответил на ping", hint="перезапустите exteraGram")


def _check_adb_and_devices(
    device_lister: Callable[[], list[str]] | None,
) -> tuple[Check, Check, list[str]]:
    """Наличие ``adb`` и список устройств в состоянии ``device``.

    ``device_lister`` подменяет :func:`catalib.deploy.adb.list_devices` в
    тестах; если он задан, реальный ``adb`` не требуется.
    """
    if device_lister is None and shutil.which("adb") is None:
        return (
            Check(
                "adb",
                WARN,
                "не найден в PATH",
                hint="установите Android platform-tools (нужно только для деплоя)",
            ),
            Check("Устройство", WARN, "пропущено — нет adb"),
            [],
        )
    adb_check = Check("adb", OK, "найден в PATH")
    lister = device_lister or list_devices
    try:
        serials = lister()
    except AdbError as exc:
        return (
            adb_check,
            Check(
                "Устройство",
                WARN,
                f"adb devices завершился ошибкой: {exc}",
                hint="перезапустите adb: adb kill-server && adb start-server",
            ),
            [],
        )
    if not serials:
        return (
            adb_check,
            Check(
                "Устройство",
                WARN,
                "нет устройств в состоянии device",
                hint="включите отладку по USB и подтвердите доверие на устройстве",
            ),
            [],
        )
    return adb_check, Check("Устройство", OK, f"подключено: {', '.join(serials)}"), serials


def _check_devserver(
    serials: list[str],
    serial: str | None,
    port: int,
    devserver_client: DevServerClient | None,
) -> Check:
    """Доступность dev server exteraGram через временный ``adb forward``.

    ``devserver_client`` подменяет реальный клиент в тестах; если он
    задан, ``adb forward`` не выполняется.
    """
    if not serials and devserver_client is None:
        return Check(
            "Dev server",
            WARN,
            "пропущено — нет устройства",
            hint="dev server проверяется при подключённом устройстве",
        )
    target = serial or (serials[0] if serials else None)
    owns_forward = devserver_client is None
    if owns_forward:
        try:
            forward_dev_server(port, target)
        except AdbError as exc:
            return Check(
                "Dev server",
                WARN,
                f"adb forward не удался: {exc}",
                hint="устройство подключено? проверьте adb devices",
            )
    client = devserver_client or DevServerClient(port=port, timeout=5.0)
    try:
        client.connect()
        answered = client.ping()
    except DevServerError as exc:
        return Check(
            "Dev server",
            WARN,
            f"недоступен: {exc}",
            hint="запустите exteraGram и включите режим разработчика",
        )
    finally:
        if owns_forward:
            client.close()
            remove_forward(port, target)
    if answered:
        return Check("Dev server", OK, f"доступен на порту {port}")
    return Check(
        "Dev server",
        WARN,
        "не ответил на ping",
        hint="перезапустите exteraGram",
    )


def _check_project(project_dir: Path) -> Check:
    """Наличие и валидность ``catalib.toml`` в каталоге проекта."""
    if not (project_dir / MANIFEST_FILENAME).is_file():
        return Check(
            "Проект",
            WARN,
            f"нет {MANIFEST_FILENAME} в {project_dir}",
            hint="запустите внутри проекта плагина или создайте: catalib init <name>",
        )
    try:
        manifest = load_manifest(project_dir)
    except ManifestError as exc:
        return Check(
            "Проект",
            FAIL,
            f"{MANIFEST_FILENAME} невалиден: {exc}",
            hint="исправьте манифест (формат — в документации)",
        )
    return Check("Проект", OK, f"{manifest.id} {manifest.version} — манифест валиден")


def run_diagnostics(
    project_dir: Path,
    *,
    serial: str | None = None,
    port: int = 42690,
    device_lister: Callable[[], list[str]] | None = None,
    devserver_client: DevServerClient | None = None,
) -> list[Check]:
    """Прогнать все проверки окружения и вернуть их результаты по порядку.

    :param project_dir: корень проекта плагина (для проверки манифеста).
    :param serial: серийный номер устройства, если их несколько.
    :param port: локальный порт для временного ``adb forward``.
    :param device_lister: подмена ``list_devices`` (тесты).
    :param devserver_client: подмена клиента dev server (тесты).
    """
    checks = [_check_python(), _check_catalib(), _check_environment()]
    if is_android():
        # На устройстве adb нет и не нужен: dev server — напрямую.
        checks.append(_check_devserver_direct(port, devserver_client))
    else:
        adb_check, device_check, serials = _check_adb_and_devices(device_lister)
        checks += [adb_check, device_check]
        checks.append(_check_devserver(serials, serial, port, devserver_client))
    checks.append(_check_project(project_dir))
    return checks


def has_failures(checks: list[Check]) -> bool:
    """Есть ли среди результатов хотя бы один :data:`FAIL`."""
    return any(check.status == FAIL for check in checks)
