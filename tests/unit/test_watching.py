"""Тесты слежения за файлами с фолбэком на поллинг (см. ADR-0011)."""

from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

from catalib import watching


def test_diff_detects_add_remove_change() -> None:
    prev = {"a": (1.0, 1), "b": (2.0, 2)}
    assert watching._diff(prev, prev) == set()
    assert watching._diff(prev, {**prev, "c": (3.0, 3)}) == {"c"}
    assert watching._diff(prev, {"a": (1.0, 1)}) == {"b"}
    assert watching._diff(prev, {**prev, "a": (9.0, 1)}) == {"a"}


def test_snapshot_lists_files(tmp_path: Path) -> None:
    (tmp_path / "x.py").write_text("1", encoding="utf-8")
    sub = tmp_path / "pkg"
    sub.mkdir()
    (sub / "y.py").write_text("22", encoding="utf-8")
    snap = watching._snapshot((tmp_path,))
    assert str(tmp_path / "x.py") in snap
    assert str(sub / "y.py") in snap


def test_backend_reflects_availability(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(watching, "_has_watchfiles", lambda: True)
    assert watching.watching_backend() == "watchfiles"
    monkeypatch.setattr(watching, "_has_watchfiles", lambda: False)
    assert watching.watching_backend() == "polling"


def test_has_watchfiles_false_when_blocked(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "watchfiles", None)
    assert watching._has_watchfiles() is False


def test_polling_yields_on_change(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "a.txt"
    target.write_text("1", encoding="utf-8")
    monkeypatch.setattr(watching, "_has_watchfiles", lambda: False)

    state = {"n": 0}

    def fake_sleep(_seconds: float) -> None:
        state["n"] += 1
        if state["n"] == 1:
            target.write_text("changed", encoding="utf-8")

    monkeypatch.setattr(watching.time, "sleep", fake_sleep)
    gen = watching.iter_changes(tmp_path, poll_interval=0.01)
    changed = next(gen)
    assert str(target) in changed


def test_polling_no_spurious_yield(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "a.txt").write_text("1", encoding="utf-8")
    monkeypatch.setattr(watching, "_has_watchfiles", lambda: False)

    state = {"n": 0}

    def fake_sleep(_seconds: float) -> None:
        state["n"] += 1
        if state["n"] >= 2:
            raise KeyboardInterrupt

    monkeypatch.setattr(watching.time, "sleep", fake_sleep)
    gen = watching.iter_changes(tmp_path, poll_interval=0.01)
    # Без изменений итератор не должен ничего отдать до прерывания.
    with pytest.raises(KeyboardInterrupt):
        next(gen)


def test_delegates_to_watchfiles(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = types.ModuleType("watchfiles")
    fake.watch = lambda *args, **kwargs: iter([{("modified", "/p/x.py")}])
    monkeypatch.setitem(sys.modules, "watchfiles", fake)
    gen = watching.iter_changes(Path("/p"))
    assert next(gen) == {"/p/x.py"}
