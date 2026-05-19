"""Высокоуровневый деплой плагина на устройство через dev server.

Два пути подключения (см. ADR-0011):

- **С ПК (по умолчанию вне Android):** ``adb forward`` локального порта
  на dev server устройства, затем подключение к ``127.0.0.1:<local_port>``.
- **На самом устройстве (Termux/Pydroid):** ``adb`` нет и не нужен —
  dev server слушает ``127.0.0.1:42690``, подключаемся к нему напрямую,
  без ``adb forward``.

Выбор пути — :func:`catalib.platforms.should_use_adb` (переопределяется
явным ``use_adb``). Последовательность обмена одинакова: ``ping`` ->
``write_plugin`` -> ``reload_plugin`` -> при первом деплое
``set_plugin_enabled(true)`` (свежий плагин регистрируется выключенным).
"""

from __future__ import annotations

from dataclasses import dataclass

from catalib.deploy.adb import forward_dev_server, remove_forward
from catalib.deploy.devserver import DevServerClient, DevServerError
from catalib.platforms import should_use_adb


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
    use_adb: bool | None = None,
    client: DevServerClient | None = None,
) -> DeployReport:
    """Доставить и перезагрузить плагин на устройстве.

    :param plugin_id: идентификатор плагина (имя файла на устройстве).
    :param content: содержимое собранного ``<plugin_id>.py``.
    :param serial: серийный номер устройства (если их несколько; только
        для пути с ``adb``).
    :param local_port: порт подключения к dev server. С ``adb`` — это
        локальный порт, пробрасываемый на устройство; без ``adb`` (на
        устройстве) — порт самого dev server (по умолчанию 42690).
    :param enable: включить плагин после записи (нужно при первом деплое).
    :param use_adb: ``True``/``False`` — явно использовать ли ``adb``;
        ``None`` — авто (на Android без ``adb``, см. ADR-0011).
    :param client: готовый клиент dev server (для тестов); если задан,
        ни ``adb forward``, ни закрытие клиента не выполняются.
    :raises DevServerError: при недоступности dev server или ошибке обмена.
    """
    owns_client = client is None
    # adb-проброс делаем только когда сами создаём соединение И среда
    # требует adb. На устройстве (Android) — подключение напрямую.
    do_forward = owns_client and should_use_adb(use_adb)
    if do_forward:
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
        if owns_client:
            active.close()
        if do_forward:
            remove_forward(local_port, serial)
