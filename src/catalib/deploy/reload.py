"""Высокоуровневый деплой плагина на устройство через dev server.

Последовательность: проброс порта ``adb forward`` -> подключение к dev
server -> ``write_plugin`` -> ``reload_plugin`` -> при первом деплое
``set_plugin_enabled(true)`` (свежий плагин регистрируется выключенным).
"""

from __future__ import annotations

from dataclasses import dataclass

from catalib.deploy.adb import forward_dev_server, remove_forward
from catalib.deploy.devserver import DevServerClient, DevServerError


@dataclass(frozen=True, slots=True)
class DeployReport:
    """Итог деплоя.

    :param plugin_id: идентификатор плагина.
    :param reloaded: плагин перезагружен на устройстве.
    :param enabled: плагин включён после деплоя.
    """

    plugin_id: str
    reloaded: bool
    enabled: bool


def deploy_plugin(
    plugin_id: str,
    content: str,
    *,
    serial: str | None = None,
    local_port: int = 42690,
    enable: bool = True,
    client: DevServerClient | None = None,
) -> DeployReport:
    """Доставить и перезагрузить плагин на устройстве.

    :param plugin_id: идентификатор плагина (имя файла на устройстве).
    :param content: содержимое собранного ``<plugin_id>.py``.
    :param serial: серийный номер устройства (если их несколько).
    :param local_port: локальный порт для ``adb forward``.
    :param enable: включить плагин после записи (нужно при первом деплое).
    :param client: готовый клиент dev server (для тестов); если задан, проброс
        порта через ``adb`` не выполняется.
    :raises DevServerError: при недоступности dev server или ошибке обмена.
    """
    owns_forward = client is None
    if owns_forward:
        forward_dev_server(local_port, serial)
    active = client or DevServerClient(port=local_port)
    try:
        active.connect()
        if not active.ping():
            raise DevServerError("dev server не ответил на ping")
        active.write_plugin(plugin_id, content)
        active.reload_plugin(plugin_id)
        if enable:
            active.set_plugin_enabled(plugin_id, True)
            active.reload_plugin(plugin_id)
        state = active.get_plugins().get(plugin_id, {})
        return DeployReport(
            plugin_id=plugin_id,
            reloaded=True,
            enabled=bool(state.get("enabled", enable)),
        )
    finally:
        if client is None:
            active.close()
        if owns_forward:
            remove_forward(local_port, serial)
