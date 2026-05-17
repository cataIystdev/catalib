"""Подпакет catalib.runtime — встраиваемый в плагин код.

Содержит загрузчик, исходник которого целиком копируется в собранный
``<plugin_id>.py``. Здесь же — доступ к этому исходнику для компилятора.
"""

from __future__ import annotations

from importlib import resources

__all__ = ["get_bootstrap_source"]


def get_bootstrap_source() -> str:
    """Вернуть исходный текст встраиваемого загрузчика ``bootstrap.py``."""
    return resources.files(__name__).joinpath("bootstrap.py").read_text(encoding="utf-8")
