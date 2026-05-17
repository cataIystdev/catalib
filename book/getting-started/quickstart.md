# Быстрый старт

За пять минут: создать модульный плагин, собрать его в один файл и
(опционально) задеплоить на устройство.

## 1. Создать проект

```bash
catalib init "Hello Plugin" --id hello --dir hello
cd hello
```

Создаётся готовый к сборке проект:

```
hello/
├── catalib.toml          # манифест: метаданные и параметры сборки
├── pyproject.toml        # конфиг pytest для офлайн-тестов
├── conftest.py
├── README.md
├── .gitignore
├── src/
│   ├── __init__.py       # корень пакета плагина
│   ├── greeting.py       # пример доменного модуля
│   └── plugin.py         # точка входа (подкласс CatalibPlugin)
└── tests/
    └── test_plugin.py    # офлайн-тест доменной логики
```

## 2. Посмотреть на точку входа

`src/plugin.py` — обычный класс плагина с автоматически регистрируемым
хуком и относительным импортом подмодуля:

```python
from catalib.support import CatalibPlugin, HookResult, HookStrategy, hook, settings

from .greeting import build_greeting


class HelloPlugin(CatalibPlugin):
    @hook.send_message
    def on_send_message_hook(self, account, params):
        message = getattr(params, "message", None)
        if not isinstance(message, str) or not message.startswith(".hello"):
            return HookResult()
        name = message[len(".hello"):].strip()
        params.message = build_greeting(name)
        return HookResult(strategy=HookStrategy.MODIFY, params=params)

    def settings(self):
        return [settings.header("Hello"), settings.text("Команда", subtext=".hello Имя")]
```

Обратите внимание: `add_on_send_message_hook()` **не нужно вызывать
вручную** — `@hook.send_message` регистрирует хук автоматически (типичная
ошибка «хук определён, но не зарегистрирован» исключена by design).

## 3. Собрать

```bash
catalib build
```

```
Собран плагин 'hello': 4 модулей
Файлы: hello/dist/hello.py, hello/dist/hello.plugin
```

`dist/hello.py` и `dist/hello.plugin` — один и тот же самодостаточный файл
в двух расширениях. Это всё, что нужно установить в exteraGram.

## 4. Прогнать офлайн-тесты

Доменная логика тестируется без Android:

```bash
pytest
```

## 5. Деплой на устройство (опционально)

Нужны: запущенный exteraGram с включённым режимом разработчика и `adb`
(см. [Подготовка устройства](../deployment/device-setup.md)).

```bash
catalib watch --deploy
```

`watch` пересобирает плагин при каждом изменении исходников и сразу
доставляет его на устройство через dev server.

## 6. Проверить в exteraGram

Включите плагин в настройках плагинов exteraGram и отправьте в любом чате:

```
.hello Мир
```

Сообщение заменится на `Привет, Мир!`.

## Дальше

- [Структура проекта](../guide/project-structure.md) — как организовывать код.
- [Манифест](../guide/manifest.md) — все поля `catalib.toml`.
- [Разбор exteraToolbox](../examples/toolbox.md) — большой пример на 44 модуля.
