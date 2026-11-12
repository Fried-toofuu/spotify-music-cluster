"""Owned, finite verification frontend; reuse the existing trusted HTTP backend."""

import os
import socket
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PORT = 7872


def main():
    with socket.socket() as probe:
        if probe.connect_ex(("127.0.0.1", PORT)) == 0:
            raise RuntimeError("Verification port 7872 already has an owner")
    env = {
        **os.environ,
        "SPOTIFY_WEB_PORT": str(PORT),
        "SPOTIFY_API_BASE_URL": "http://127.0.0.1:8000",
        "GRADIO_ANALYTICS_ENABLED": "False",
    }
    code = """
import sys
from spotify_cluster.web.app import create_app, launch_options
app = create_app()
app.launch(prevent_thread_lock=True, **launch_options())
try:
    sys.stdin.read(1)
finally:
    app.close()
"""
    process = subprocess.Popen(
        [sys.executable, "-c", code],
        cwd=ROOT,
        env=env,
        stdin=subprocess.PIPE,
        text=True,
    )
    print(
        f"Owned verification frontend PID {process.pid}; port {PORT}; workspace {ROOT}",
        flush=True,
    )
    try:
        sys.stdin.read(1)
    finally:
        if process.poll() is None:
            process.stdin.write("\n")
            process.stdin.flush()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


if __name__ == "__main__":
    main()
