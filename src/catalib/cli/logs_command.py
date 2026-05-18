"""Команда ``catalib logs`` — logcat устройства, отфильтрованный по плагину."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from catalib.deploy.adb import AdbError, logcat
from catalib.devicelogs import filter_log
from catalib.manifest.loader import load_manifest
from catalib.manifest.model import ManifestError


def logs(
    project: Annotated[
        Path, typer.Option("--project", "-p", help="Каталог проекта плагина")
    ] = Path(),
    serial: Annotated[
        str | None, typer.Option("--serial", help="Серийный номер устройства")
    ] = None,
    lines: Annotated[
        int, typer.Option("--lines", "-n", help="Сколько последних строк logcat читать")
    ] = 100,
    clear: Annotated[
        bool, typer.Option("--clear", help="Очистить буфер логов перед чтением")
    ] = False,
    show_all: Annotated[
        bool, typer.Option("--all", help="Не фильтровать по плагину — весь logcat")
    ] = False,
    pattern: Annotated[
        str | None,
        typer.Option("--filter", help="Фильтр-подстрока (по умолчанию plugin_id)"),
    ] = None,
) -> None:
    """Показать логи устройства, отфильтрованные по текущему плагину.

    По умолчанию фильтр — ``plugin_id`` из ``catalib.toml`` проекта
    (плагины логируют как ``[plugin_id] ...``). ``--filter`` задаёт свою
    подстроку, ``--all`` отключает фильтр. Поведение совпадает с
    инструментом MCP ``adb_get_logs``.
    """
    try:
        text = logcat(lines, serial, clear=clear)
    except AdbError as exc:
        typer.secho(f"Ошибка logs: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc

    if show_all:
        needle = ""
    elif pattern:
        needle = pattern
    else:
        try:
            needle = load_manifest(project.resolve()).id
        except ManifestError:
            typer.secho(
                "Нет валидного catalib.toml — показываю весь logcat "
                "(укажите --filter или --all явно).",
                fg=typer.colors.YELLOW,
                err=True,
            )
            needle = ""

    typer.echo(filter_log(text, needle))
