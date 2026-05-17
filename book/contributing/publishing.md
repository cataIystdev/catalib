# Публикация в PyPI

Как выпустить `catalib`, чтобы пользователи ставили его `pip install catalib`.

## Готовность пакета

Проект уже сконфигурирован для публикации (`pyproject.toml`, backend
`hatchling`):

- метаданные: `name`, `version`, `description`, `readme`, `license`,
  `authors`, `keywords`, `classifiers`, `requires-python = ">=3.11"`;
- `[project.urls]` указывают на GitHub-репозиторий;
- консольная команда: `[project.scripts] catalib = "catalib.cli.app:main"`;
- в дистрибутив попадают все встраиваемые файлы
  (`catalib/runtime/bootstrap.py`, `catalib/support/*`);
- дополнительная группа `publish` — `build` и `twine`.

Имя `catalib` на PyPI свободно (на момент подготовки).

## Сборка дистрибутивов

```bash
pip install -e ".[publish]"     # build + twine
python -m build                 # создаёт dist/*.whl и dist/*.tar.gz
python -m twine check dist/*    # проверка метаданных пакета
```

`python -m build` должен завершиться `Successfully built
catalib-X.Y.Z.tar.gz and catalib-X.Y.Z-py3-none-any.whl`,
`twine check` — `PASSED`.

## Тест на TestPyPI (рекомендуется)

```bash
python -m twine upload --repository testpypi dist/*
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ catalib
catalib version
```

## Публикация на PyPI

### Вариант A: API-токен + twine

1. Зарегистрируйтесь на [pypi.org](https://pypi.org), включите 2FA.
2. Account settings → API tokens → создать токен (scope: весь аккаунт для
   первого релиза, потом — на проект).
3. Загрузка:

   ```bash
   python -m twine upload dist/*
   # имя пользователя: __token__
   # пароль: pypi-AgEI...  (значение токена)
   ```

   Либо положите токен в `~/.pypirc`:

   ```ini
   [pypi]
   username = __token__
   password = pypi-AgEI...
   ```

### Вариант B: Trusted Publishing (рекомендуется для CI)

Без хранения токенов: PyPI доверяет конкретному GitHub Actions workflow
через OIDC.

1. На PyPI: проект → Settings → Publishing → добавить «trusted publisher»
   (owner `cataIystdev`, repo `catalib`, workflow `release.yml`,
   environment `pypi`).
2. Workflow `.github/workflows/release.yml`:

```yaml
name: release
on:
  push:
    tags: ["v*"]
jobs:
  build-and-publish:
    runs-on: ubuntu-latest
    environment: pypi
    permissions:
      id-token: write          # обязательно для OIDC
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install build
      - run: python -m build
      - uses: pypa/gh-action-pypi-publish@release/v1
```

Тогда релиз = пуш git-тега `vX.Y.Z`.

## Версионирование и теги

Проект следует SemVer; `CHANGELOG.md` ведётся по Keep a Changelog.
Чеклист релиза:

1. Перенести содержимое `[Unreleased]` в раздел `## [X.Y.Z] - ГГГГ-ММ-ДД`.
2. Обновить `version` в `pyproject.toml` и `src/catalib/__init__.py`
   (оба должны совпадать).
3. Зелёные `ruff` и `pytest`.
4. `python -m build && python -m twine check dist/*`.
5. Коммит `chore(release): версия X.Y.Z`, тег `git tag -a vX.Y.Z`.
6. Публикация (twine или пуш тега при Trusted Publishing).

## Важно про вендоринг

`catalib.support` вшивается в собираемые плагины. После релиза с
исправлениями `support` пользователям нужно **пересобрать** свои плагины
новой версией catalib, чтобы получить фиксы. Это стоит упоминать в
release notes.

## Что не коммитить

`dist/`, `build/`, `*.egg-info/`, `.venv/` уже в `.gitignore`. Артефакты
сборки и токены в репозиторий не попадают.
