"""Обёртки модуля SDK ``client_utils``.

Очереди, сетевые запросы, отправка и редактирование сообщений, геттеры
контроллеров Telegram, подписка на уведомления. На устройстве вызывается
настоящий ``client_utils``; вне приложения — функциональные офлайн-заглушки
с честным контрактом: ``run_on_queue`` офлайн выполняет callable немедленно
(чтобы логика плагина прогонялась в тестах), отправки фиксируются в
:data:`_sent`, геттеры контроллеров возвращают ``None``. На устройстве
всегда работает настоящий SDK. Зависит только от стандартной библиотеки и
SDK.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

# Константы очередей (значения совпадают с client_utils).
STAGE_QUEUE = "stageQueue"
GLOBAL_QUEUE = "globalQueue"
CACHE_CLEAR_QUEUE = "cacheClearQueue"
SEARCH_QUEUE = "searchQueue"
PHONE_BOOK_QUEUE = "phoneBookQueue"
THEME_QUEUE = "themeQueue"
EXTERNAL_NETWORK_QUEUE = "externalNetworkQueue"
PLUGINS_QUEUE = "pluginsQueue"

#: Допустимые режимы разметки текста.
_PARSE_MODES = (None, "HTML", "Markdown")

#: Офлайн-журнал отправок/запросов (для проверок в тестах).
_sent: list[tuple[Any, ...]] = []
#: Офлайн-журнал постановок в очередь.
_queue_runs: list[tuple[str, int]] = []
_request_seq = 0


def _client_attr(name: str) -> Any:
    """Вернуть атрибут настоящего ``client_utils`` либо ``None`` офлайн."""
    try:  # pragma: no cover - на устройстве
        import client_utils

        return getattr(client_utils, name, None)
    except Exception:
        return None


def _check_parse_mode(parse_mode: str | None) -> None:
    """Проверить режим разметки; бросить ``ValueError`` при неизвестном."""
    if parse_mode not in _PARSE_MODES:
        raise ValueError(f"неподдерживаемый parse_mode: {parse_mode!r}")


def run_on_queue(
    func: Callable[[], Any], queue_name: str = PLUGINS_QUEUE, delay_ms: int = 0
) -> Any:
    """Выполнить работу вне UI-потока.

    :param func: вызываемый объект без аргументов.
    :param queue_name: имя очереди (по умолчанию :data:`PLUGINS_QUEUE`).
    :param delay_ms: задержка в миллисекундах (офлайн игнорируется).
    :returns: на устройстве — результат SDK; офлайн — результат ``func()``
        (вызов выполняется немедленно, чтобы логика тестировалась).
    """
    real = _client_attr("run_on_queue")
    if real is not None:  # pragma: no cover - на устройстве
        return real(func, queue_name, delay_ms)
    _queue_runs.append((queue_name, delay_ms))
    return func()


def get_queue_by_name(queue_name: str) -> Any:
    """Вернуть ``DispatchQueue`` по имени (офлайн — ``None``)."""
    real = _client_attr("get_queue_by_name")
    return real(queue_name) if real is not None else None


def send_request(request: Any, callback: Callable[[Any, Any], None] | None = None) -> Any:
    """Отправить сырой запрос Telegram API.

    :param request: TL-объект запроса.
    :param callback: ``callback(response, error)``.
    :returns: идентификатор запроса (офлайн — синтетический ``int``).
    """
    real = _client_attr("send_request")
    if real is not None:  # pragma: no cover - на устройстве
        return real(request, callback)
    global _request_seq
    _request_seq += 1
    _sent.append(("request", request))
    return _request_seq


def _send(real_name: str, kind: str, *args: Any) -> Any:
    """Делегировать отправку на устройство либо зафиксировать офлайн."""
    real = _client_attr(real_name)
    if real is not None:  # pragma: no cover - на устройстве
        return real(*args)
    _sent.append((kind, *args))
    return None


def send_text(
    peer_id: Any, message: str, replyToMsg: Any = None, parse_mode: str | None = None
) -> Any:
    """Отправить текстовое сообщение."""
    return _send("send_text", "text", peer_id, message, replyToMsg, parse_mode)


def send_photo(
    peer_id: Any,
    photo_path: str,
    caption: str | None = None,
    high_quality: bool = False,
    parse_mode: str | None = None,
) -> Any:
    """Отправить фото с необязательной подписью."""
    return _send(
        "send_photo", "photo", peer_id, photo_path, caption, high_quality, parse_mode
    )


def send_document(
    peer_id: Any, file_path: str, caption: str | None = None, parse_mode: str | None = None
) -> Any:
    """Отправить файл-документ."""
    return _send("send_document", "document", peer_id, file_path, caption, parse_mode)


def send_video(
    peer_id: Any, video_path: str, caption: str | None = None, parse_mode: str | None = None
) -> Any:
    """Отправить видео (метаданные SDK заполняет сам)."""
    return _send("send_video", "video", peer_id, video_path, caption, parse_mode)


def send_audio(
    peer_id: Any, audio_path: str, caption: str | None = None, parse_mode: str | None = None
) -> Any:
    """Отправить аудио (метаданные SDK заполняет сам)."""
    return _send("send_audio", "audio", peer_id, audio_path, caption, parse_mode)


def send_message(params: dict[str, Any], parse_mode: str | None = None) -> Any:
    """Низкоуровневая отправка по словарю ``SendMessageParams``."""
    return _send("send_message", "message", params, parse_mode)


def edit_message(
    message_obj: Any,
    text: str | None = None,
    file_path: str | None = None,
    with_spoiler: bool = False,
    parse_mode: str | None = None,
) -> Any:
    """Отредактировать существующий ``MessageObject``.

    :raises ValueError: при неподдерживаемом ``parse_mode`` (как в SDK).
    """
    _check_parse_mode(parse_mode)
    real = _client_attr("edit_message")
    if real is not None:  # pragma: no cover - на устройстве
        return real(message_obj, text, file_path, with_spoiler, parse_mode)
    _sent.append(("edit", message_obj, text, file_path, with_spoiler, parse_mode))
    return None


def _controller(name: str) -> Any:
    """Вернуть контроллер с текущего аккаунта (офлайн — ``None``)."""
    real = _client_attr(name)
    return real() if real is not None else None


def get_last_fragment() -> Any:
    """Текущий фрагмент UI (офлайн — ``None``)."""
    return _controller("get_last_fragment")


def get_account_instance() -> Any:
    """Экземпляр текущего аккаунта (офлайн — ``None``)."""
    return _controller("get_account_instance")


def get_messages_controller() -> Any:
    """``MessagesController`` — состояние и запросы (офлайн — ``None``)."""
    return _controller("get_messages_controller")


def get_contacts_controller() -> Any:
    """``ContactsController`` (офлайн — ``None``)."""
    return _controller("get_contacts_controller")


def get_media_data_controller() -> Any:
    """``MediaDataController`` (офлайн — ``None``)."""
    return _controller("get_media_data_controller")


def get_connections_manager() -> Any:
    """``ConnectionsManager`` (офлайн — ``None``)."""
    return _controller("get_connections_manager")


def get_location_controller() -> Any:
    """``LocationController`` (офлайн — ``None``)."""
    return _controller("get_location_controller")


def get_notifications_controller() -> Any:
    """``NotificationsController`` (офлайн — ``None``)."""
    return _controller("get_notifications_controller")


def get_messages_storage() -> Any:
    """``MessagesStorage`` (поле ``.database``) (офлайн — ``None``)."""
    return _controller("get_messages_storage")


def get_send_messages_helper() -> Any:
    """``SendMessagesHelper`` (офлайн — ``None``)."""
    return _controller("get_send_messages_helper")


def get_file_loader() -> Any:
    """``FileLoader`` (офлайн — ``None``)."""
    return _controller("get_file_loader")


def get_secret_chat_helper() -> Any:
    """``SecretChatHelper`` (офлайн — ``None``)."""
    return _controller("get_secret_chat_helper")


def get_download_controller() -> Any:
    """``DownloadController`` (офлайн — ``None``)."""
    return _controller("get_download_controller")


def get_notifications_settings() -> Any:
    """``NotificationsSettings`` (офлайн — ``None``)."""
    return _controller("get_notifications_settings")


def get_notification_center() -> Any:
    """``NotificationCenter`` — подписки (офлайн — ``None``)."""
    return _controller("get_notification_center")


def get_media_controller() -> Any:
    """``MediaController`` (офлайн — ``None``)."""
    return _controller("get_media_controller")


def get_user_config() -> Any:
    """``UserConfig`` (офлайн — ``None``)."""
    return _controller("get_user_config")


try:  # pragma: no cover - ветка выполняется только на устройстве
    from client_utils import NotificationCenterDelegate
except Exception:  # pragma: no cover - ветка для обычного Python

    class NotificationCenterDelegate:
        """Офлайн-база делегата ``NotificationCenter``.

        Подкласс переопределяет ``didReceivedNotification(id, account,
        args)``. Офлайн базовая реализация — no-op.
        """

        def didReceivedNotification(
            self, id: int, account: int, args: Any
        ) -> None:
            """Получено уведомление (офлайн — ничего не делает)."""


__all__ = [
    "CACHE_CLEAR_QUEUE",
    "EXTERNAL_NETWORK_QUEUE",
    "GLOBAL_QUEUE",
    "PHONE_BOOK_QUEUE",
    "PLUGINS_QUEUE",
    "SEARCH_QUEUE",
    "STAGE_QUEUE",
    "THEME_QUEUE",
    "NotificationCenterDelegate",
    "edit_message",
    "get_account_instance",
    "get_connections_manager",
    "get_contacts_controller",
    "get_download_controller",
    "get_file_loader",
    "get_last_fragment",
    "get_location_controller",
    "get_media_controller",
    "get_media_data_controller",
    "get_messages_controller",
    "get_messages_storage",
    "get_notification_center",
    "get_notifications_controller",
    "get_notifications_settings",
    "get_queue_by_name",
    "get_secret_chat_helper",
    "get_send_messages_helper",
    "get_user_config",
    "run_on_queue",
    "send_audio",
    "send_document",
    "send_message",
    "send_photo",
    "send_request",
    "send_text",
    "send_video",
]
