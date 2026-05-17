# Настройки

Экран настроек плагина описывается декларативно через модуль
`catalib.support.settings`. Метод `settings()` возвращает список
элементов; `CatalibPlugin` сам строит требуемый SDK `create_settings()`.

```python
from catalib.support import CatalibPlugin, settings


class P(CatalibPlugin):
    def settings(self):
        return [
            settings.header("Мой плагин"),
            settings.switch("enabled", "Включено", default=True),
            settings.text_input("token", "Токен", subtext="секретное значение"),
            settings.text("Подсказка", subtext="Отправьте .help"),
        ]
```

## Конструкторы элементов

| Функция | Назначение |
|---------|------------|
| `settings.header(text)` | заголовок секции |
| `settings.switch(key, text, default=False, subtext="")` | булев переключатель |
| `settings.text_input(key, text, default="", subtext="", icon="")` | поле ввода |
| `settings.text(text, subtext="", icon="")` | информационная строка (без значения) |

`key` — ключ, под которым значение хранится; читается методом
`get_setting(key, default)`.

## Чтение значений

```python
class P(CatalibPlugin):
    def settings(self):
        return [settings.text_input("prefix", "Префикс", default=".")]

    def on_load(self):
        self.prefix = self.get_setting("prefix", ".")
```

Изменения настроек пользователь делает в UI exteraGram; читать значение
лучше в момент использования (например в обработчике хука), чтобы
подхватывать актуальное:

```python
@hook.send_message
def on_send_message_hook(self, account, params):
    prefix = self.get_setting("prefix", ".")
    ...
```

## Как это работает офлайн и на устройстве

`settings.*` возвращает объекты `SettingItem` (тип элемента + параметры).
Метод `SettingItem.build()`:

- **на устройстве** — конвертирует в соответствующий класс `ui.settings`
  exteraGram (`Header`, `Switch`, `Input`, `Text`);
- **офлайн** (нет SDK) — возвращает сам элемент.

Поэтому форму настроек можно проверять в обычных тестах:

```python
def test_settings():
    items = MyPlugin().create_settings()
    assert [getattr(i, "kind", None) for i in items] == ["header", "switch"]
```

## Полный пример

```python
from catalib.support import CatalibPlugin, settings

PREFIX = "prefix"

class P(CatalibPlugin):
    def settings(self):
        return [
            settings.header("Калькулятор"),
            settings.text_input(PREFIX, "Префикс команд", default=".",
                                subtext="Например . или !"),
            settings.switch("show_errors", "Показывать ошибки", default=True),
            settings.text("Использование", subtext=".calc 2+2"),
        ]

    def on_load(self):
        # значения доступны сразу после включения плагина
        self.prefix = self.get_setting(PREFIX, ".")
```
