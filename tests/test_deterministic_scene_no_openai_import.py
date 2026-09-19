"""Regression: deterministic Scene -> LEGO imports do not load OpenAI."""
from __future__ import annotations

import builtins
import subprocess
import sys
from pathlib import Path


def test_partial_scene_pipeline_import_does_not_require_or_load_openai() -> None:
    backend = Path(__file__).parents[1] / "backend"
    script = r"""
import builtins
import sys

real_import = builtins.__import__

def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
    if name == "openai" or name.startswith("openai."):
        raise AssertionError(f"deterministic Scene -> LEGO path imported {name}")
    return real_import(name, globals, locals, fromlist, level)

builtins.__import__ = guarded_import
from brickhouse.partial_scene_pipeline import run_partial_scene_pipeline
assert callable(run_partial_scene_pipeline)
assert "brickhouse.vision.openai_provider" not in sys.modules
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=Path(__file__).parents[1],
        env={"PYTHONPATH": str(backend)},
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
