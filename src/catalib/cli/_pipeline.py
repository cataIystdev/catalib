"""Конвейер сборки, переиспользуемый командами ``build`` и ``watch``.

Объединяет шаги: загрузка манифеста, обход исходников, компиляция в один
файл. Все доменные ошибки приводятся к единому :class:`BuildFailure`.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from catalib.bundler.compiler import CompilerError, compile_plugin
from catalib.bundler.discovery import discover_sources
from catalib.bundler.model import BundleResult, DiscoveryError
from catalib.bundler.requirements import RequirementsError
from catalib.manifest.loader import load_manifest
from catalib.manifest.metadata import MetadataError
from catalib.manifest.model import ManifestError, PluginManifest


class BuildFailure(RuntimeError):
    """Единая ошибка сборки с человекочитаемым сообщением для CLI."""


@dataclass(frozen=True, slots=True)
class BuildOutcome:
    """Результат конвейера сборки."""

    manifest: PluginManifest
    bundle: BundleResult
    #: Основной выходной файл ``<plugin_id>.py``.
    output_path: Path
    #: Идентичная копия с расширением ``.plugin`` (для установки в exteraGram).
    plugin_path: Path


def build_bundle(project_dir: Path, *, write: bool = True) -> BuildOutcome:
    """Собрать плагин из проекта.

    :param project_dir: корень проекта плагина (с ``catalib.toml``).
    :param write: записать ли результат в каталог ``build.out``.
    :raises BuildFailure: при любой ошибке манифеста, обхода, зависимостей,
        компиляции или валидации метаданных.
    """
    try:
        manifest = load_manifest(project_dir)
        src_dir = project_dir / manifest.build.src
        tree = discover_sources(src_dir, manifest.build.entry)
        bundle = compile_plugin(manifest, tree)
    except (
        ManifestError,
        DiscoveryError,
        RequirementsError,
        CompilerError,
        MetadataError,
    ) as exc:
        raise BuildFailure(str(exc)) from exc

    out_dir = project_dir / manifest.build.out
    output_path = out_dir / bundle.filename
    plugin_path = out_dir / f"{manifest.id}.plugin"
    if write:
        out_dir.mkdir(parents=True, exist_ok=True)
        # Идентичное содержимое в двух расширениях: .py для разработки и
        # совместимости, .plugin для установки в exteraGram.
        output_path.write_text(bundle.text, encoding="utf-8")
        plugin_path.write_text(bundle.text, encoding="utf-8")
    return BuildOutcome(
        manifest=manifest,
        bundle=bundle,
        output_path=output_path,
        plugin_path=plugin_path,
    )
