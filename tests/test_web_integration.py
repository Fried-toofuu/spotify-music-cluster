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
        [sys.executable, str(root / "plans/20261112-gradio-web/verify-http.py")],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=90,
    )
    assert result.returncode == 0, result.stderr
    evidence = json.loads(
        (root / "plans/20261112-gradio-web/reports/http-smoke.json").read_text()
    )
    assert evidence["status"] == "PASS"
    assert evidence["private_sample_agreement"] and evidence["gradio_http_prediction"]
    assert evidence["offline_feedback"]
    assert all(evidence["ports_released"].values())
