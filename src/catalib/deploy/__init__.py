"""Подпакет catalib.deploy — доставка плагина на устройство.

Канал доставки — встроенный dev server exteraGram (TCP 42690) с пробросом
порта через ``adb forward``; прямой ``adb push`` без root запрещён (ADR-0004).
"""

from __future__ import annotations

from catalib.deploy.adb import AdbError, list_devices
from catalib.deploy.devserver import DevServerClient, DevServerError
from catalib.deploy.reload import DeployReport, deploy_plugin

__all__ = [
    "AdbError",
    "DeployReport",
    "DevServerClient",
    "DevServerError",
    "deploy_plugin",
    "list_devices",
]
