"""Type stubs for the exteraGram SDK module ``ui.bulletin``."""

from collections.abc import Callable
from typing import Any

class BulletinHelper:
    DURATION_SHORT: int
    DURATION_LONG: int
    DURATION_PROLONG: int
    @classmethod
    def show_info(cls, message: str, fragment: Any = ...) -> None: ...
    @classmethod
    def show_error(cls, message: str, fragment: Any = ...) -> None: ...
    @classmethod
    def show_success(cls, message: str, fragment: Any = ...) -> None: ...
    @classmethod
    def show_simple(
        cls, message: str, icon_res_id: int, duration: int = ..., fragment: Any = ...
    ) -> None: ...
    @classmethod
    def show_two_line(
        cls,
        title: str,
        subtitle: str,
        icon_res_id: int,
        duration: int = ...,
        fragment: Any = ...,
    ) -> None: ...
    @classmethod
    def show_with_button(
        cls,
        message: str,
        icon_res_id: int,
        button_text: str,
        on_click: Callable[[], Any],
        duration: int = ...,
        fragment: Any = ...,
    ) -> None: ...
    @classmethod
    def show_undo(
        cls,
        subtitle: str,
        on_undo: Callable[[], Any],
        on_action: Callable[[], Any] | None = ...,
        fragment: Any = ...,
    ) -> None: ...
    @classmethod
    def show_copied_to_clipboard(cls, fragment: Any = ...) -> None: ...
    @classmethod
    def show_link_copied(cls, is_private_link: bool = ..., fragment: Any = ...) -> None: ...
    @classmethod
    def show_file_saved_to_gallery(cls, is_video: bool = ..., fragment: Any = ...) -> None: ...
    @classmethod
    def show_file_saved_to_downloads(
        cls, amount: int = ..., file_type: Any = ..., fragment: Any = ...
    ) -> None: ...
