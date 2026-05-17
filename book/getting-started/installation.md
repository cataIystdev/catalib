# Установка

## Требования

- **Python 3.11 и новее** на машине разработчика. Это совпадает со средой
  Chaquopy внутри exteraGram (Python 3.11) — собранный плагин гарантированно
  совместим с целевым рантаймом.
- `adb` (Android platform-tools) — только если планируется деплой на
  устройство (`catalib watch --deploy`). Для сборки `adb` не нужен.

Внешние зависимости самого инструмента: `typer` (CLI) и `watchfiles`
(слежение за файлами). Они ставятся автоматически вместе с пакетом.

## Установка из PyPI

```bash
pip install catalib
```

После установки доступна команда `catalib`:

```bash
catalib version
catalib --help
```

## Установка из исходников

```bash
git clone https://github.com/cataIystdev/catalib.git
cd catalib
pip install .
```

## Установка для разработки

Редактируемая установка с инструментами тестирования и линтинга:

```bash
git clone https://github.com/cataIystdev/catalib.git
cd catalib
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Группы дополнительных зависимостей:

| Группа | Команда | Содержимое |
|--------|---------|------------|
| `dev` | `pip install -e ".[dev]"` | `pytest`, `pytest-cov`, `ruff` |
| `publish` | `pip install -e ".[publish]"` | `build`, `twine` (для выпуска в PyPI) |

## Проверка установки

```bash
catalib version          # печатает версию catalib
catalib init "Проба" --id proba --dir /tmp/proba
catalib build --project /tmp/proba
ls /tmp/proba/dist       # proba.py и proba.plugin
```

Если всё прошло — переходите к [быстрому старту](quickstart.md).

## Изоляция окружения

catalib не требует доступа к устройству для сборки и не исполняет код
собираемого плагина (только статический разбор через `ast`), поэтому его
безопасно запускать в CI и в чистом виртуальном окружении.
