"""Загрузка манифеста плагина из ``catalib.toml``.

Манифест читается стандартным ``tomllib`` и нормализуется в
:class:`~catalib.manifest.model.PluginManifest`. Все ошибки формата
поднимаются как :class:`~catalib.manifest.model.ManifestError` с понятным
сообщением, указывающим на проблемное поле.
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from catalib.manifest.model import BuildConfig, ManifestError, PluginManifest

#: Имя файла манифеста в корне проекта плагина.
MANIFEST_FILENAME = "catalib.toml"

_REQUIRED_PLUGIN_KEYS = ("id", "name", "version")
_ALLOWED_PLUGIN_KEYS = (
    "id",
    "name",
    "version",
    "description",
    "author",
    "icon",
    "min_version",
    "sdk_version",
    "requirements",
)
_ALLOWED_BUILD_KEYS = ("src", "entry", "out", "vendor")


def _ensure_str(table: str, key: str, value: Any) -> str:
    """Проверить, что значение — строка, иначе поднять ManifestError."""
    if not isinstance(value, str):
        raise ManifestError(f"{table}.{key} должен быть строкой, получено {type(value).__name__}")
    return value


def _parse_build(raw: Any) -> BuildConfig:
    """Построить :class:`BuildConfig` из таблицы ``[build]`` (или значений по умолчанию)."""
    if raw is None:
        return BuildConfig()
    if not isinstance(raw, dict):
        raise ManifestError("секция [build] должна быть таблицей")
    unknown = set(raw) - set(_ALLOWED_BUILD_KEYS)
    if unknown:
        raise ManifestError(f"неизвестные ключи в [build]: {', '.join(sorted(unknown))}")
    defaults = BuildConfig()
    return BuildConfig(
        src=_ensure_str("build", "src", raw.get("src", defaults.src)),
        entry=_ensure_str("build", "entry", raw.get("entry", defaults.entry)),
        out=_ensure_str("build", "out", raw.get("out", defaults.out)),
        vendor=_ensure_str("build", "vendor", raw.get("vendor", defaults.vendor)),
    )


def _parse_requirements(raw: Any) -> tuple[str, ...]:
    """Нормализовать ``plugin.requirements`` в кортеж строк."""
    if raw is None:
        return ()
    if not isinstance(raw, list) or not all(isinstance(item, str) for item in raw):
        raise ManifestError("plugin.requirements должен быть списком строк")
    return tuple(raw)


def parse_manifest(data: dict[str, Any]) -> PluginManifest:
    """Построить :class:`PluginManifest` из разобранного TOML-словаря.

    :param data: словарь верхнего уровня манифеста.
    :raises ManifestError: при отсутствии обязательных секций/полей, неизвестных
        ключах или неверных типах.
    """
    if "plugin" not in data:
        raise ManifestError("в манифесте отсутствует обязательная секция [plugin]")
    plugin = data["plugin"]
    if not isinstance(plugin, dict):
        raise ManifestError("секция [plugin] должна быть таблицей")

    unknown = set(plugin) - set(_ALLOWED_PLUGIN_KEYS)
    if unknown:
        raise ManifestError(f"неизвестные ключи в [plugin]: {', '.join(sorted(unknown))}")
    missing = [key for key in _REQUIRED_PLUGIN_KEYS if key not in plugin]
    if missing:
        raise ManifestError(f"в [plugin] нет обязательных ключей: {', '.join(missing)}")

    unknown_top = set(data) - {"plugin", "build"}
    if unknown_top:
        raise ManifestError(f"неизвестные секции верхнего уровня: {', '.join(sorted(unknown_top))}")

    return PluginManifest(
        id=_ensure_str("plugin", "id", plugin["id"]),
        name=_ensure_str("plugin", "name", plugin["name"]),
        version=_ensure_str("plugin", "version", plugin["version"]),
        description=_ensure_str("plugin", "description", plugin.get("description", "")),
        author=_ensure_str("plugin", "author", plugin.get("author", "")),
        icon=_ensure_str("plugin", "icon", plugin.get("icon", "")),
        min_version=_ensure_str("plugin", "min_version", plugin.get("min_version", "")),
        sdk_version=_ensure_str("plugin", "sdk_version", plugin.get("sdk_version", "")),
        requirements=_parse_requirements(plugin.get("requirements")),
        build=_parse_build(data.get("build")),
    )


def load_manifest_text(text: str) -> PluginManifest:
    """Разобрать манифест из строки TOML."""
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise ManifestError(f"ошибка разбора TOML: {exc}") from exc
    return parse_manifest(data)


def load_manifest(project_dir: Path) -> PluginManifest:
    """Загрузить и проверить ``catalib.toml`` из каталога проекта.

    :param project_dir: корень проекта плагина.
    :raises ManifestError: если файл отсутствует или невалиден.
    """
    manifest_path = project_dir / MANIFEST_FILENAME
    if not manifest_path.is_file():
        raise ManifestError(f"не найден {MANIFEST_FILENAME} в {project_dir}")
    return load_manifest_text(manifest_path.read_text(encoding="utf-8"))
