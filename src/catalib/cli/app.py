"""Точка входа CLI ``catalib`` (typer).

Команды:

- ``build`` — собрать модульный плагин в один файл;
- ``watch`` — пересобирать при изменениях, опционально деплоить;
- ``init`` — создать шаблон модульного плагина.
"""

from __future__ import annotations

import typer

from catalib import __version__
from catalib.cli.build_command import build
from catalib.cli.init_command import init
from catalib.cli.watch_command import watch_command

app = typer.Typer(
    name="catalib",
    help="Сборка модульных плагинов exteraGram в один файл.",
    no_args_is_help=True,
    add_completion=False,
)

app.command("build")(build)
app.command("init")(init)
app.command("watch")(watch_command)


@app.command("version")
def version() -> None:
    """Показать версию catalib."""
    typer.echo(__version__)


def main() -> None:
    """Консольная точка входа (см. ``project.scripts`` в pyproject)."""
    app()


if __name__ == "__main__":
    main()
