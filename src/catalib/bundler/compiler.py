"""Компилятор: сборка дерева исходников в один ``<plugin_id>.py``.

Структура выходного файла:

1. Литералы метаданных exteraGram (читаются движком через AST).
2. Встроенный загрузчик (исходник :mod:`catalib.runtime.bootstrap`).
3. Таблица встроенных исходников и имя точки входа.
4. Вызов ``catalib_install(...)``, активирующий загрузчик.

Метаданные эмитятся строго строковыми литералами — это требование
AST-парсера exteraGram (динамические значения не читаются).
"""

from __future__ import annotations

from catalib.bundler.model import BundleResult, SourceTree
from catalib.bundler.requirements import merge_requirements
from catalib.bundler.sourcemap import build_source_map, runtime_fullname
from catalib.manifest.metadata import validate_metadata
from catalib.manifest.model import PluginManifest

_HEADER = (
    "# Файл сгенерирован catalib (https://github.com/cataIystdev/catalib)"
    " из модульного дерева исходников.\n"
    "# Редактировать вручную не следует: правьте исходники и пересоберите.\n"
)


class CompilerError(ValueError):
    """Ошибка компиляции выходного файла плагина."""


def _metadata_block(manifest: PluginManifest) -> str:
    """Сформировать блок дандеров строковыми литералами."""
    lines = [
        f"__id__ = {manifest.id!r}",
        f"__name__ = {manifest.name!r}",
        f"__version__ = {manifest.version!r}",
        f"__description__ = {manifest.description!r}",
        f"__author__ = {manifest.author!r}",
    ]
    if manifest.icon:
        lines.append(f"__icon__ = {manifest.icon!r}")
    if manifest.min_version:
        # Только канонический дандер exteraGram. Нестандартный
        # __min_version__ не эмитится: exteraGram показывает на него
        # отдельный экран несовместимости.
        lines.append(f"__app_version__ = {manifest.min_version!r}")
    if manifest.sdk_version:
        lines.append(f"__sdk_version__ = {manifest.sdk_version!r}")
    return "\n".join(lines) + "\n"


def _requirements_block(requirements: tuple[str, ...]) -> str:
    """Сформировать литерал ``__requirements__`` (только если непусто)."""
    if not requirements:
        return ""
    items = ", ".join(repr(item) for item in requirements)
    return f"__requirements__ = [{items}]\n"


def _sources_block(manifest: PluginManifest, tree: SourceTree, vendor_modules: tuple) -> str:
    """Сформировать таблицу встроенных исходников и имя точки входа.

    Таблица включает модули плагина (под именами ``<plugin_id>.*``) и
    отобранные вендоренные модули ``catalib`` (под их настоящими именами),
    так как на устройстве пакет ``catalib`` не установлен.
    """
    origins = build_source_map(manifest.id, tree)
    entries = []
    for module in tree.modules:
        fullname = runtime_fullname(manifest.id, module.relname)
        origin = origins[fullname]
        entries.append(f"    {fullname!r}: ({module.source!r}, {module.is_package!r}, {origin!r}),")
    for module in vendor_modules:
        origin = f"<catalib-vendor>/{module.relpath}"
        entries.append(
            f"    {module.relname!r}: ({module.source!r}, {module.is_package!r}, {origin!r}),"
        )
    table = "_CATALIB_SOURCES = {\n" + "\n".join(entries) + "\n}\n"
    entry_fullname = runtime_fullname(manifest.id, tree.entry)
    table += f"_CATALIB_ENTRY = {entry_fullname!r}\n"
    return table


def compile_plugin(manifest: PluginManifest, tree: SourceTree) -> BundleResult:
    """Собрать выходной файл плагина.

    :param manifest: проверенный манифест плагина.
    :param tree: дерево исходников (из :func:`discover_sources`).
    :raises CompilerError: если результат синтаксически невалиден или
        метаданные не проходят AST-проверку.
    """
    from catalib.bundler.treeshake import plan_vendor
    from catalib.runtime import get_bootstrap_source

    requirements = merge_requirements(manifest.requirements, tree.modules)
    plan = plan_vendor(tree, manifest.build.vendor)

    parts = [
        _HEADER,
        _metadata_block(manifest),
        _requirements_block(requirements),
        "\n",
        get_bootstrap_source(),
        "\n",
        _sources_block(manifest, tree, plan.modules),
        "\n",
        # Идентификатор передаётся литералом: к этому моменту глобальный
        # __name__ уже перетёрт литералом метаданных __name__.
        f"catalib_install({manifest.id!r}, globals(), _CATALIB_SOURCES, _CATALIB_ENTRY)\n",
    ]
    text = "".join(parts)

    try:
        compile(text, manifest.output_filename, "exec")
    except SyntaxError as exc:
        raise CompilerError(f"собранный файл синтаксически невалиден: {exc}") from exc

    validate_metadata(text, expected_id=manifest.id)

    return BundleResult(
        text=text,
        filename=manifest.output_filename,
        requirements=requirements,
        module_count=len(tree.modules),
        vendored_kept=plan.kept,
        vendored_pruned=plan.pruned,
        vendor_full=plan.full,
        vendor_warnings=plan.warnings,
    )
