# catalib init

Создаёт каркас модульного плагина, готовый к `catalib build`.

```bash
catalib init NAME [--id ID] [--dir DIR] [--author AUTHOR] [--template T]
```

## Аргументы и опции

| Аргумент/опция | По умолчанию | Назначение |
|----------------|--------------|------------|
| `NAME` | — (обязателен) | отображаемое имя плагина |
| `--id` | производится из `NAME` | идентификатор плагина (валидируется) |
| `--dir`, `-d` | `= ID` | каталог проекта |
| `--author` | пусто | автор плагина |
| `--template`, `-t` | `hook` | шаблон проекта (см. ниже) |

## Шаблоны

Все шаблоны собираются без правок и несут офлайн-тест; различается точка
входа и доменный модуль.

| `--template` | Что внутри |
|--------------|-----------|
| `hook` (по умолчанию) | хук исходящих сообщений `.hello <имя>` + настройки; доменный модуль `greeting.py` |
| `minimal` | голый `CatalibPlugin` (только `on_load` + заголовок настроек); `core.py` |
| `menu` | пункт контекстного меню сообщения; доменный модуль `actions.py` |
| `settings` | поведение управляется настройками (switch + text_input) в хуке; `format.py` |

Тесты шаблонов `menu` и `settings` используют
[`catalib.testing`](../guide/testing.md) — хук/меню вызываются как в SDK,
без устройства.

`--id` по умолчанию получается из `NAME`: нижний регистр, недопустимые
символы → `_`, обрезка до 32, гарантия старта с буквы. Лучше задавать явно.

## Что создаётся

Структура шаблона по умолчанию (`hook`):

```
<dir>/
├── catalib.toml          # манифест (id, name, version=1.0.0, ...)
├── pyproject.toml        # pytest: pythonpath=["."]
├── conftest.py
├── README.md
├── .gitignore            # dist/, __pycache__/
├── src/
│   ├── __init__.py
│   ├── greeting.py       # доменный модуль (пример, тестируется офлайн)
│   └── plugin.py         # точка входа: CatalibPlugin + хук + настройки
└── tests/
    └── test_plugin.py    # офлайн-тест build_greeting
```

Сгенерированный проект **собирается без правок** и демонстрирует
относительный импорт подмодуля (`from .greeting import build_greeting`).

## Пример

```bash
$ catalib init "Hello Plugin" --id hello --dir hello --author "catalyst"
Создан проект плагина 'hello' (шаблон 'hook') в /path/hello
Файлов: 9. Сборка: catalib build --project /path/hello

$ catalib init "Menu Plugin" --id menup --template menu
Создан проект плагина 'menup' (шаблон 'menu') в /path/menup
Файлов: 9. Сборка: catalib build --project /path/menup
```

## Ошибки

| Сообщение | Причина |
|-----------|---------|
| `Ошибка init: plugin_id '...' невалиден` | id не подходит под `^[a-z][a-z0-9_]{1,31}$` |
| `Ошибка init: имя плагина не должно быть пустым` | пустой `NAME` |
| `Ошибка init: каталог ... не пуст` | целевой каталог существует и не пуст |
| `Ошибка init: неизвестный шаблон '...'` | `--template` не из списка (`hook`, `menu`, `minimal`, `settings`) |

## Дальше

```bash
cd hello
catalib build          # dist/hello.py + dist/hello.plugin
pytest                 # офлайн-тесты доменной логики
```
