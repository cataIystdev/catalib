"""Команда ``catalib stubs`` — установка type-стабов SDK в проект."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from catalib.sdk_stubs import install_stubs


def stubs(
    directory: Annotated[
        Path,
        typer.Option("--dir", "-d", help="Каталог для стабов (по умолчанию typings)"),
    ] = Path("typings"),
    force: Annotated[bool, typer.Option("--force", help="Перезаписать существующие стабы")] = False,
) -> None:
    """Скопировать ``.pyi``-стабы SDK exteraGram в проект для автодополнения.

    Pyright/Pylance подхватывают каталог ``typings/`` автоматически. Для
    mypy добавьте его в ``mypy_path``.
    """
    dest = directory.resolve()
    try:
        written = install_stubs(dest, force=force)
    except FileExistsError as exc:
        typer.secho(f"Ошибка stubs: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc

    typer.secho(f"Установлено стабов: {len(written)} в {dest}", fg=typer.colors.GREEN)
    typer.echo("Pyright/Pylance используют typings/ автоматически. Для mypy: mypy_path = typings")
