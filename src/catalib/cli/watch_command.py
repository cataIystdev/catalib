"""Команда ``catalib watch`` — пересборка по изменению и автодеплой."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from catalib.cli._pipeline import BuildFailure, build_bundle
from catalib.deploy.devserver import DevServerError
from catalib.deploy.reload import deploy_plugin
from catalib.manifest.loader import load_manifest
from catalib.manifest.model import ManifestError
from catalib.watching import iter_changes, watching_backend


def _rebuild(
    project: Path,
    do_deploy: bool,
    serial: str | None,
    port: int,
    use_adb: bool | None = None,
) -> None:
    """Одна итерация пересборки (и опционально деплоя) с выводом статуса."""
    try:
        outcome = build_bundle(project, write=True)
    except BuildFailure as exc:
        typer.secho(f"Сборка не удалась: {exc}", fg=typer.colors.RED, err=True)
        return
    typer.secho(
        f"Собрано: {outcome.output_path} ({outcome.bundle.module_count} модулей)",
        fg=typer.colors.GREEN,
    )
    if not do_deploy:
        return
    try:
        report = deploy_plugin(
            outcome.manifest.id,
            outcome.bundle.text,
            serial=serial,
            local_port=port,
            use_adb=use_adb,
        )
    except DevServerError as exc:
        typer.secho(f"Деплой не удался: {exc}", fg=typer.colors.RED, err=True)
        return
    typer.secho(
        f"Задеплоено на устройство (включён={report.enabled})",
        fg=typer.colors.GREEN,
    )


def watch_command(
    project: Annotated[
        Path, typer.Option("--project", "-p", help="Каталог проекта плагина")
    ] = Path(),
    deploy: Annotated[
        bool, typer.Option("--deploy", help="Деплоить на устройство после сборки")
    ] = False,
    serial: Annotated[
        str | None, typer.Option("--serial", help="Серийный номер устройства")
    ] = None,
    port: Annotated[
        int,
        typer.Option(
            "--port",
            help="Порт dev server: локальный для adb forward либо прямой на устройстве",
        ),
    ] = 42690,
    adb: Annotated[
        bool | None,
        typer.Option(
            "--adb/--no-adb",
            help="Использовать adb для деплоя (по умолчанию авто: на устройстве без adb)",
        ),
    ] = None,
    poll: Annotated[
        float,
        typer.Option("--poll", help="Интервал поллинга, с (только без watchfiles)"),
    ] = 1.0,
) -> None:
    """Следить за исходниками и пересобирать плагин при изменениях.

    Слежение использует ``watchfiles`` (если установлен) либо stdlib-
    поллинг — команда работает и без ``watchfiles`` (важно на Termux/
    Pydroid, где Rust-бэкенд не собрать; см. ADR-0011).
    """
    project = project.resolve()
    try:
        manifest = load_manifest(project)
    except ManifestError as exc:
        typer.secho(f"Невалидный манифест: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc

    src_dir = project / manifest.build.src
    manifest_path = project / "catalib.toml"
    typer.echo(
        f"Слежу за {src_dir} и {manifest_path} (бэкенд: {watching_backend()}). Ctrl+C — выход."
    )
    _rebuild(project, deploy, serial, port, adb)
    try:
        for _changes in iter_changes(src_dir, manifest_path, poll_interval=poll):
            _rebuild(project, deploy, serial, port, adb)
    except KeyboardInterrupt:
        typer.echo("Остановлено.")
