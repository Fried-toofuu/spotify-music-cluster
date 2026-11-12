"""Construction and import isolation using the public Blocks configuration."""

import os
import subprocess
import sys

import pytest


def test_application_constructs_offline():
    from spotify_cluster.web.app import create_app, theme

    app = create_app()
    config = app.config
    tabs = [c["props"]["label"] for c in config["components"] if c["type"] == "tabitem"]
    assert tabs == [
        "Overview",
        "Predict Cluster",
        "Cluster Explorer",
        "Research & Methodology",
    ]
    names = {d["api_name"] for d in config["dependencies"]}
    assert {"refresh", "refresh_live_data", "predict_cluster"} <= names
    assert len(config["dependencies"]) == 8
    assert theme().body_background_fill == "#141b18"


def test_imports_do_not_load_model_dataset_or_start_servers(tmp_path):
    script = """
import sys
import gradio, uvicorn
def forbidden(*a, **k):
    raise AssertionError("server started during import/construction")
gradio.Blocks.launch = forbidden
uvicorn.Server.run = forbidden
def audit(event, args):
    if event == "open" and isinstance(args[0], str):
        assert not args[0].endswith((".csv", ".joblib", ".ipynb"))
sys.addaudithook(audit)
from spotify_cluster.web.app import create_app
create_app()
for name in ("training", "model_store", "inference", "data"):
    assert "spotify_cluster." + name not in sys.modules, name
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=tmp_path,
        env={**os.environ, "GRADIO_ANALYTICS_ENABLED": "False"},
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr


def test_bracketed_ipv6_no_proxy_entries_do_not_break_gradio_import(tmp_path):
    script = """
import os
os.environ["NO_PROXY"] = "localhost,[::1],127.0.0.1"
import spotify_cluster.web
assert os.environ["NO_PROXY"] == "localhost,::1,127.0.0.1"
import gradio
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=tmp_path,
        env={**os.environ, "GRADIO_ANALYTICS_ENABLED": "False"},
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr


def test_launch_policy_rejects_environment_file_allowances(monkeypatch):
    from spotify_cluster.web.app import launch_options

    monkeypatch.delenv("GRADIO_ALLOWED_PATHS", raising=False)
    options = launch_options()
    assert options["share"] is False and options["run_history"] is False
    assert options["server_port"] == 7860 and options["allowed_paths"] == []
    monkeypatch.setenv("GRADIO_ALLOWED_PATHS", "D:/private")
    with pytest.raises(ValueError, match="Remove GRADIO_ALLOWED_PATHS"):
        launch_options()
