"""FQN-константы часто используемых Java-классов Telegram/Android.

Чистые данные (строки), без зависимости от SDK — доступны всегда, и на
устройстве, и офлайн. Удобно для ``find_class``/``@xposed``/рефлексии
вместо «магических строк». Значения соответствуют разделу документации
common-source-classes.
"""

from __future__ import annotations

#: Инициализация приложения, обработка deep links.
LAUNCH_ACTIVITY = "org.telegram.ui.LaunchActivity"
#: Профиль пользователя и канала.
PROFILE_ACTIVITY = "org.telegram.ui.ProfileActivity"
#: Интерфейс чата.
CHAT_ACTIVITY = "org.telegram.ui.ChatActivity"
#: Рендеринг отдельного сообщения.
CHAT_MESSAGE_CELL = "org.telegram.ui.Cells.ChatMessageCell"
#: Обёртка над TLRPC.Message.
MESSAGE_OBJECT = "org.telegram.messenger.MessageObject"
#: Набор Android-утилит (dp(), runOnUIThread() ...).
ANDROID_UTILITIES = "org.telegram.messenger.AndroidUtilities"
#: Управление состоянием и Telegram-запросами.
MESSAGES_CONTROLLER = "org.telegram.messenger.MessagesController"
#: Локальная БД; поле .database для SQLite-запросов.
MESSAGES_STORAGE = "org.telegram.messenger.MessagesStorage"
#: Отправка всех типов сообщений и файлов.
SEND_MESSAGES_HELPER = "org.telegram.messenger.SendMessagesHelper"
#: Создание bulletin-уведомлений.
BULLETIN_FACTORY = "org.telegram.ui.Components.BulletinFactory"
#: Модальные диалоги поверх фрагмента.
ALERT_DIALOG = "org.telegram.ui.ActionBar.AlertDialog"
#: TL-объекты запросов и ответов Telegram.
TLRPC = "org.telegram.tgnet.TLRPC"

#: Сопоставление короткого имени класса с его FQN.
COMMON_CLASSES: dict[str, str] = {
    "LaunchActivity": LAUNCH_ACTIVITY,
    "ProfileActivity": PROFILE_ACTIVITY,
    "ChatActivity": CHAT_ACTIVITY,
    "ChatMessageCell": CHAT_MESSAGE_CELL,
    "MessageObject": MESSAGE_OBJECT,
    "AndroidUtilities": ANDROID_UTILITIES,
    "MessagesController": MESSAGES_CONTROLLER,
    "MessagesStorage": MESSAGES_STORAGE,
    "SendMessagesHelper": SEND_MESSAGES_HELPER,
    "BulletinFactory": BULLETIN_FACTORY,
    "AlertDialog": ALERT_DIALOG,
    "TLRPC": TLRPC,
}

__all__ = [
    "ALERT_DIALOG",
    "ANDROID_UTILITIES",
    "BULLETIN_FACTORY",
    "CHAT_ACTIVITY",
    "CHAT_MESSAGE_CELL",
    "COMMON_CLASSES",
    "LAUNCH_ACTIVITY",
    "MESSAGES_CONTROLLER",
    "MESSAGES_STORAGE",
    "MESSAGE_OBJECT",
    "PROFILE_ACTIVITY",
    "SEND_MESSAGES_HELPER",
    "TLRPC",
]
