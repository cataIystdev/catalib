"""Дымовой тест каркаса пакета.

Проверяет, что пакет импортируется и объявляет корректную строковую версию.
Служит минимальным набором, подтверждающим работоспособность окружения тестов.
"""

import catalib


def test_package_exposes_version() -> None:
    """Пакет должен предоставлять непустую строковую версию."""
    assert isinstance(catalib.__version__, str)
    assert catalib.__version__.count(".") == 2


def test_runnable_as_module() -> None:
    """``python -m catalib`` должен делегировать в ту же точку входа CLI."""
    from catalib.__main__ import main as module_main
    from catalib.cli.app import main as cli_main

    assert module_main is cli_main
