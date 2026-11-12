"""Opt-in existing-artifact HTTP integration. No dataset access or training."""

import json
import subprocess
import sys
from pathlib import Path

import pytest


def test_real_gradio_http(request):
    if not request.config.getoption("--run-real-web"):
        pytest.skip("Private deployment HTTP check requires --run-real-web")
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [
            sys.executable,
            str(root / "plans/20261112-acoustic-observatory/verify-live.py"),
        ],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=360,
    )
    assert result.returncode == 0, result.stderr
    evidence = json.loads(
        (root / "plans/20261112-acoustic-observatory/reports/browser.json").read_text()
    )
    assert evidence["status"] == "PASS"
    assert len(evidence["viewports"]) == 3
    assert evidence["checks"]["keyboard"] == "PASS"
    assert evidence["checks"]["focus-outline"] == "PASS"
    assert evidence["checks"]["reduced-motion"] == "PASS"
    assert evidence["errors"] == []
    assert evidence["private_features_logged"] is False
    assert all(evidence["ports_released"].values())
