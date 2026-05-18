"""Сквозной тест: сгенерированный проект проходит свой ``pytest``.

Проверяет всю цепочку блока C: шаблон -> сгенерированный
``tests/test_plugin.py`` -> реальный :mod:`catalib.testing`. ``pytest``
запускается в каталоге проекта отдельным процессом (как у разработчика).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from catalib.scaffold import create_project


@pytest.mark.parametrize("template", ["hook", "minimal", "menu", "settings"])
def test_generated_project_tests_pass(tmp_path: Path, template: str) -> None:
    project = tmp_path / template
    create_project(project, "demo", "Demo", author="catalyst", template=template)
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q"],
        capture_output=True,
        text=True,
        cwd=project,
    )
    assert proc.returncode == 0, f"stdout={proc.stdout}\nstderr={proc.stderr}"
