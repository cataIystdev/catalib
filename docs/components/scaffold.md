# Компонент: scaffold

Назначение: генерация шаблона модульного плагина (`catalib init`).

## Состав

- `templates.py` — шаблоны файлов (`catalib.toml`, `pyproject.toml`,
  `src/__init__.py`, `src/greeting.py`, `src/plugin.py`,
  `tests/test_plugin.py`, README, `.gitignore`, `conftest.py`).
- `__init__.py` — `create_project` (валидация `plugin_id`, отказ при непустом
  каталоге, вывод класса из `plugin_id`); `ScaffoldError`.

Сгенерированный проект собирается `catalib build` без правок и содержит
относительный импорт подмодуля (демонстрация модульности) и офлайн-тест
доменной логики.

## Связи

- Зависит от: `manifest` (паттерн `plugin_id`).
- Используется: `cli.init`.
- Связанные документы: [cli](cli.md), [bundler](bundler.md).
