"""Команда ``catalib doctor`` — префлайт-диагностика окружения."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from catalib.diagnostics import FAIL, OK, WARN, has_failures, run_diagnostics

_LABEL = {OK: "OK  ", WARN: "WARN", FAIL: "FAIL"}
_COLOR = {OK: typer.colors.GREEN, WARN: typer.colors.YELLOW, FAIL: typer.colors.RED}


def doctor(
    project: Annotated[
        Path, typer.Option("--project", "-p", help="Каталог проекта плагина")
    ] = Path(),
    serial: Annotated[
        str | None, typer.Option("--serial", help="Серийный номер устройства")
    ] = None,
    port: Annotated[int, typer.Option("--port", help="Локальный порт для adb forward")] = 42690,
) -> None:
    """Проверить готовность окружения к сборке и деплою плагинов.

    Код возврата 1 — только при критических проблемах (старый Python,
    битый ``catalib.toml``). Отсутствие устройства или dev server —
    предупреждение: для сборки они не нужны.
    """
    checks = run_diagnostics(project.resolve(), serial=serial, port=port)
    for check in checks:
        typer.secho(
            f"[{_LABEL[check.status]}] {check.name}: {check.detail}",
            fg=_COLOR[check.status],
        )
        if check.hint and check.status != OK:
            typer.echo(f"        -> {check.hint}")
    if has_failures(checks):
        typer.secho(
            "Есть критические проблемы — устраните их перед сборкой.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)
    typer.secho("Окружение готово.", fg=typer.colors.GREEN)
