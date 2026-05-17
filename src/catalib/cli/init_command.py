"""Команда ``catalib init`` — генерация шаблона модульного плагина."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Annotated

import typer

from catalib.scaffold import ScaffoldError, create_project


def _default_plugin_id(name: str) -> str:
    """Построить корректный ``plugin_id`` из имени проекта."""
    slug = re.sub(r"[^a-z0-9_]+", "_", name.lower()).strip("_")
    slug = re.sub(r"_+", "_", slug)
    if not slug or not slug[0].isalpha():
        slug = f"p_{slug}" if slug else "plugin"
    return slug[:32]


def init(
    name: Annotated[str, typer.Argument(help="Отображаемое имя плагина")],
    directory: Annotated[
        Path | None,
        typer.Option("--dir", "-d", help="Каталог проекта (по умолчанию = plugin_id)"),
    ] = None,
    plugin_id: Annotated[
        str | None,
        typer.Option("--id", help="Идентификатор плагина (по умолчанию из имени)"),
    ] = None,
    author: Annotated[str, typer.Option("--author", help="Автор плагина")] = "",
) -> None:
    """Создать каркас модульного плагина, готовый к ``catalib build``."""
    resolved_id = plugin_id or _default_plugin_id(name)
    target = (directory or Path(resolved_id)).resolve()
    try:
        created = create_project(target, resolved_id, name, author)
    except ScaffoldError as exc:
        typer.secho(f"Ошибка init: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc

    typer.secho(f"Создан проект плагина {resolved_id!r} в {target}", fg=typer.colors.GREEN)
    typer.echo(f"Файлов: {len(created)}. Сборка: catalib build --project {target}")
