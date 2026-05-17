# Компонент: manifest

Назначение: модель и валидация манифеста плагина `catalib.toml`, а также
статическая (AST) проверка метаданных собранного файла.

## Состав

- `model.py` — `PluginManifest`, `BuildConfig`, инварианты (`PLUGIN_ID_PATTERN`,
  `VERSION_PATTERN`, `CONSTRAINT_PATTERN`), исключение `ManifestError`.
- `loader.py` — чтение `catalib.toml` через `tomllib`, строгая проверка
  секций/ключей/типов.
- `metadata.py` — `extract_metadata` (как читает exteraGram) и
  `validate_metadata` (литеральность дандеров, совпадение `__id__` с именем
  файла, формат версии), исключение `MetadataError`.

## Связи

- Зависит от: стандартная библиотека (`tomllib`, `ast`, `re`).
- Используется: `bundler.compiler` (валидация метаданных), `cli._pipeline`,
  `scaffold` (паттерн `plugin_id`).
- Связанные документы: [bundler](bundler.md),
  [ADR-0002](../architecture/decisions/ADR-0002-bundler-meta-path.md),
  [глоссарий](../glossary.md).
