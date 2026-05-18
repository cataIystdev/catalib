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

Полный паритет с `ui.settings` (ADR-0006):

| Функция | Назначение |
|---------|------------|
| `settings.header(text)` | заголовок секции |
| `settings.divider(text="")` | разделитель с необязательной подписью |
| `settings.switch(key, text, default=False, subtext="")` | булев переключатель |
| `settings.selector(key, text, default, items)` | выпадающий список |
| `settings.text_input(key, text, default="", subtext="", icon="")` | однострочный ввод (Input) |
| `settings.edit_text(key, hint, default="")` | многострочный ввод (EditText) |
| `settings.text(text, subtext="", icon="")` | строка (кликабельная при `on_click=`) |
| `settings.custom(...)` | кастомная строка (`item`/`view`/`factory`) |

`key` — ключ, под которым значение хранится; читается методом
`get_setting(key, default)`.

### Необязательные параметры (keyword-only)

Доступны там, где их поддерживает SDK: `on_click`, `on_change`,
`on_long_click`, `icon`, `accent`, `red`, `link_alias`,
`create_sub_fragment` (Text/Custom), `multiline`/`max_length`/`mask`
(EditText). Прежние позиционные вызовы не изменились — новые параметры
попадают в SDK только когда заданы.

```python
settings.text("Запустить", on_click=self._launch)          # кликабельная
settings.text("Удалить всё", red=True, on_click=self._wipe)
settings.selector("mode", "Режим", 0, ["A", "B"], on_change=self._on_mode)
settings.edit_text("note", "Заметка", multiline=True, max_length=500)
```

Кликабельная строка теперь первоклассна — ручной перебор API клика в
плагине не нужен.

### `simple_setting_factory`

Обёртка `ui.settings.SimpleSettingFactory` для строки `custom`:

```python
factory = settings.simple_setting_factory(create_view, bind_view,
                                           is_clickable=True)
settings.custom(factory=factory)
```

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
  exteraGram (`Header`, `Divider`, `Switch`, `Selector`, `Input`,
  `EditText`, `Text`, `Custom`);
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
