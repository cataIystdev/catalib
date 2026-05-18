"""Точка входа CLI ``catalib`` (typer).

Команды:

- ``build`` — собрать модульный плагин в один файл;
- ``watch`` — пересобирать при изменениях, опционально деплоить;
- ``init`` — создать шаблон модульного плагина.
"""

from __future__ import annotations

import typer

from catalib import __version__, check_for_updates
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


def _notify_update() -> None:
    """Сообщить (в stderr), если на PyPI есть более новая версия catalib.

    Полностью безопасна: :func:`catalib.check_for_updates` не делает
    сетевых запросов чаще раза в сутки, не бросает исключений и
    отключается ``CATALIB_NO_UPDATE_CHECK=1``. Команда не падает при любом
    исходе проверки.
    """
    try:
        newer = check_for_updates()
    except Exception:
        return
    if newer:
        typer.secho(
            f"Доступна новая версия catalib {newer} (установлена "
            f"{__version__}). Обновить: pip install -U catalib. "
            f"Отключить проверку: CATALIB_NO_UPDATE_CHECK=1.",
            fg=typer.colors.YELLOW,
            err=True,
        )


def main() -> None:
    """Консольная точка входа (см. ``project.scripts`` в pyproject)."""
    _notify_update()
    app()


if __name__ == "__main__":
    main()
