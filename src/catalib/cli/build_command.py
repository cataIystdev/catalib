"""Команда ``catalib build`` — сборка плагина в один файл."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from catalib.cli._pipeline import BuildFailure, build_bundle


def build(
    project: Annotated[
        Path,
        typer.Option("--project", "-p", help="Каталог проекта плагина"),
    ] = Path(),
    check: Annotated[
        bool,
        typer.Option("--check", help="Только проверить сборку, не записывать файл"),
    ] = False,
) -> None:
    """Собрать модульный плагин в один ``<plugin_id>.py``."""
    try:
        outcome = build_bundle(project.resolve(), write=not check)
    except BuildFailure as exc:
        typer.secho(f"Ошибка сборки: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc

    bundle = outcome.bundle
    typer.secho(
        f"Собран плагин {outcome.manifest.id!r}: {bundle.module_count} модулей",
        fg=typer.colors.GREEN,
    )
    if bundle.requirements:
        typer.echo(f"Зависимости: {', '.join(bundle.requirements)}")
    if bundle.vendor_full:
        typer.echo(f"Вендоринг catalib: полный ({len(bundle.vendored_kept)} модулей)")
        for warning in bundle.vendor_warnings:
            typer.secho(f"  причина: {warning}", fg=typer.colors.YELLOW)
    else:
        typer.echo(
            f"Вендоринг catalib: отобрано {len(bundle.vendored_kept)}, "
            f"отсечено {len(bundle.vendored_pruned)}"
        )
    if check:
        typer.echo("Проверка пройдена (файлы не записаны, --check).")
    else:
        typer.echo(f"Файлы: {outcome.output_path}, {outcome.plugin_path}")
