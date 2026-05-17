"""Сквозной тест: init → build → исполнение в чистом интерпретаторе.

Собранный плагин исполняется отдельным процессом интерпретатора без
установленного ``catalib`` — это проверяет вендоринг ``catalib.support``,
относительные импорты и мини-фреймворк ровно так, как на устройстве.
"""

from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path

from catalib.cli._pipeline import build_bundle
from catalib.scaffold import create_project

_RUNNER = textwrap.dedent(
    """
    import importlib.util, sys

    # Заблокировать host-catalib: вендоренный пакет внутри bundle обязан
    # обслуживаться его собственным finder'ом (как на устройстве, где
    # catalib не установлен). Finder bundle вставляется в meta_path[0]
    # на этапе exec_module, поэтому до этого блокировщика дело не доходит.
    for _m in [n for n in list(sys.modules) if n == "catalib" or n.startswith("catalib.")]:
        del sys.modules[_m]

    class _BlockHostCatalib:
        def find_spec(self, name, path=None, target=None):
            if name == "catalib" or name.startswith("catalib."):
                raise ModuleNotFoundError("host catalib заблокирован: " + name)
            return None

    sys.meta_path.append(_BlockHostCatalib())

    path, plugin_id = sys.argv[1], sys.argv[2]
    spec = importlib.util.spec_from_file_location(plugin_id, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[plugin_id] = module
    spec.loader.exec_module(module)

    plugin_cls = module.GreetPlugin
    inst = plugin_cls()
    inst.on_plugin_load()

    class Params:
        message = ".hello Боб"

    params = Params()
    result = inst.on_send_message_hook(0, params)
    assert params.message == "Привет, Боб!", params.message
    assert result.strategy == "MODIFY", result.strategy
    assert ("send_message", 0) in inst.registered_hooks, inst.registered_hooks
    print("CATALIB_OK")
    """
)


def test_scaffolded_plugin_runs_via_vendored_support(tmp_path: Path) -> None:
    """init → build → исполнение в подпроцессе с заблокированным host-catalib.

    Блокировка host-catalib гарантирует, что ``catalib.support`` берётся из
    вендоренного кода внутри собранного файла — ровно как на устройстве.
    """
    project = tmp_path / "greet_proj"
    create_project(project, "greet", "Greet", author="catalyst")
    outcome = build_bundle(project, write=True)
    bundle_path = outcome.output_path
    assert bundle_path.is_file()

    runner = tmp_path / "runner.py"
    runner.write_text(_RUNNER, encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(runner), str(bundle_path), "greet"],
        capture_output=True,
        text=True,
        cwd=tmp_path,
        env={"PYTHONPATH": ""},
    )
    assert proc.returncode == 0, f"stdout={proc.stdout}\nstderr={proc.stderr}"
    assert "CATALIB_OK" in proc.stdout
