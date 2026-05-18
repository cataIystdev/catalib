"""Поддержка ``python -m catalib`` — эквивалент консольной команды.

Делегирует в ту же точку входа, что и ``project.scripts`` (см.
pyproject), поэтому проверка обновлений и поведение CLI идентичны.
"""

from __future__ import annotations

from catalib.cli.app import main

if __name__ == "__main__":
    main()
