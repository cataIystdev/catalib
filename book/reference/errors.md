# Исключения

Все ошибки несут человекочитаемое сообщение. CLI приводит их к коду
возврата `1` и печатает в stderr с префиксом (`Ошибка сборки: ...`).

## Среда инструмента (сборка)

| Исключение | Модуль | Когда возникает |
|------------|--------|-----------------|
| `ManifestError` | `catalib.manifest.model` | нет `catalib.toml`/секции/обязательных ключей; неизвестный ключ; неверный тип; невалидные `id`/`version`/ограничения версий |
| `MetadataError` | `catalib.manifest.metadata` | метаданные собранного файла не литеральны / не совпал `__id__` / неверный `__version__` / синтаксис |
| `DiscoveryError` | `catalib.bundler.model` | нет каталога `src`; пусто; каталог с модулями без `__init__.py`; path traversal; не найден модуль точки входа |
| `RequirementsError` | `catalib.bundler.requirements` | бинарный пакет в `__requirements__`; пустое требование |
| `CompilerError` | `catalib.bundler.compiler` | собранный файл синтаксически невалиден / не прошёл AST-проверку |
| `ScaffoldError` | `catalib.scaffold` | невалидный `plugin_id`; пустое имя; непустой целевой каталог |
| `BuildFailure` | `catalib.cli._pipeline` | единая обёртка над ошибками конвейера для CLI |

## Деплой

| Исключение | Модуль | Когда возникает |
|------------|--------|-----------------|
| `AdbError` | `catalib.deploy.adb` | `adb` не найден; команда `adb` завершилась с ошибкой |
| `DevServerError` | `catalib.deploy.devserver` | не удалось подключиться к dev server; таймаут/ошибка обмена |

## Иерархия

`ManifestError`, `MetadataError`, `DiscoveryError`, `RequirementsError`,
`CompilerError`, `ScaffoldError` — наследники `ValueError`.
`BuildFailure` — `RuntimeError` (CLI ловит именно её).
`AdbError`, `DevServerError` — `RuntimeError`.

## Пример обработки в скрипте

```python
from pathlib import Path
from catalib.cli._pipeline import build_bundle, BuildFailure

try:
    outcome = build_bundle(Path("my_plugin"))
    print(outcome.output_path, outcome.plugin_path)
except BuildFailure as exc:
    print("сборка не удалась:", exc)
    raise SystemExit(1)
```
