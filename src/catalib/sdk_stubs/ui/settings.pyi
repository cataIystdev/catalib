"""Type stubs for the exteraGram SDK module ``ui.settings``."""

from collections.abc import Callable
from typing import Any

class Header:
    def __init__(self, text: str) -> None: ...

class Divider:
    def __init__(self, text: str = ...) -> None: ...

class Switch:
    def __init__(
        self,
        key: str,
        text: str,
        default: bool = ...,
        subtext: str = ...,
        icon: str = ...,
        on_change: Callable[[bool], Any] | None = ...,
        link_alias: str = ...,
    ) -> None: ...

class Selector:
    def __init__(
        self,
        key: str,
        text: str,
        default: int,
        items: list[str],
        icon: str = ...,
        on_change: Callable[[int], Any] | None = ...,
    ) -> None: ...

class Input:
    def __init__(
        self,
        key: str,
        text: str,
        default: str = ...,
        subtext: str = ...,
        icon: str = ...,
        on_change: Callable[[str], Any] | None = ...,
        link_alias: str = ...,
    ) -> None: ...

class EditText:
    def __init__(
        self,
        key: str,
        hint: str,
        default: str = ...,
        multiline: bool = ...,
        max_length: int = ...,
        mask: str = ...,
        on_change: Callable[[str], Any] | None = ...,
    ) -> None: ...

class Text:
    def __init__(
        self,
        text: str,
        subtext: str = ...,
        icon: str = ...,
        accent: bool = ...,
        red: bool = ...,
        on_click: Callable[[], Any] | None = ...,
        create_sub_fragment: Callable[[], Any] | None = ...,
        link_alias: str = ...,
    ) -> None: ...

class Custom:
    def __init__(
        self,
        item: Any = ...,
        view: Any = ...,
        factory: Any = ...,
        factory_args: Any = ...,
        on_click: Callable[[], Any] | None = ...,
    ) -> None: ...
