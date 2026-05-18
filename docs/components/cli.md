# Компонент: cli

Назначение: пользовательский интерфейс командной строки (typer).

## Состав

- `_pipeline.py` — конвейер `build_bundle` (манифест → обход → компиляция),
  единая ошибка `BuildFailure`, `BuildOutcome`.
- `build_command.py` — `catalib build [--project] [--check]`.
- `watch_command.py` — `catalib watch [--project] [--deploy] [--serial]
  [--port]` (слежение через `watchfiles`). `watchfiles` — опциональная
  зависимость (группа `watch`); импортируется лениво в `_load_watch()`, при
  отсутствии — понятная ошибка с подсказкой `pip install "catalib[watch]"`.
  `build`/`init`/`version` работают без `watchfiles`. См. ADR-0005.
- `init_command.py` — `catalib init NAME [--id] [--dir] [--author]`.
- `app.py` — сборка `typer.Typer`, точка входа `main`, команда `version`.

## Связи

- Зависит от: `manifest`, `bundler`, `deploy`, `scaffold`, `typer`;
  `watchfiles` — опционально, только команда `watch` (ADR-0005).
- Используется: консольная точка входа `catalib` (`project.scripts`).
- Связанные документы: [bundler](bundler.md), [deploy](deploy.md),
  [scaffold](scaffold.md),
  [ADR-0005](../architecture/decisions/ADR-0005-watchfiles-optional.md).
