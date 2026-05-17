# История изменений

Полная история ведётся в `CHANGELOG.md` в корне репозитория по формату
[Keep a Changelog](https://keepachangelog.com/ru/1.1.0/); проект следует
[Semantic Versioning](https://semver.org/lang/ru/).

Актуальная версия:
[CHANGELOG.md на GitHub](https://github.com/cataIystdev/catalib/blob/main/CHANGELOG.md).

## Заметные вехи

- Сборка модульного дерева в один самодостаточный `<plugin_id>.py`
  (CLI `build`), плюс идентичная копия `<plugin_id>.plugin`.
- Встроенный загрузчик на `sys.meta_path`: относительные импорты,
  пакеты, трейсбеки на исходники; очистка устаревших вендоренных
  `catalib.*` между деплоями.
- Мини-фреймворк `catalib.support`: авто-регистрация хуков и пунктов
  меню, типизированные настройки, безопасные импорты SDK.
- CLI `watch` с автодеплоем через dev server, `init` с шаблоном.
- Корректный API меню SDK (`MenuItemData(menu_type=..., on_click=...)`),
  отказ от нестандартного `__min_version__`.
- Пример `exteraToolbox` (44 модуля) и полная документация (эта книга).
