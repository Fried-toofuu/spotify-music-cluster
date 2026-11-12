"""Real loopback HTTP verification; retains no private input rows. No model fitting."""

import json
import os
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORTS = Path(__file__).resolve().parent / "reports"
ARTIFACT = ROOT / "artifacts" / "deployment-v1"
PORT = 8000


def serve():
    import uvicorn

    from spotify_cluster.api.app import app

    server = uvicorn.Server(
        uvicorn.Config(
            app,
            host="127.0.0.1",
            port=PORT,
            access_log=False,
        )
    )

    def stop_on_stdin():
        sys.stdin.read(1)
        server.should_exit = True

    # Import native numerical extensions before blocking a thread on Windows stdin.
    threading.Thread(target=stop_on_stdin, daemon=True).start()
    server.run()


def verify():
    import httpx
    import numpy as np

    from spotify_cluster.config import F9

    # Refuse to start a duplicate or interfere with any pre-existing port owner.
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", PORT))
    sample = json.loads((ARTIFACT / "verification_sample.json").read_text())
    metadata = json.loads((ARTIFACT / "metadata.json").read_text())
    tracks = [dict(zip(F9, row, strict=True)) for row in sample["raw_f9"]]
    environment = {**os.environ, "SPOTIFY_MODEL_DIR": str(ARTIFACT)}
    evidence = {"status": "FAIL", "port": PORT, "worktree": str(ROOT), "statuses": {}}
    log_path = REPORTS / "http-server.txt"
    with log_path.open("w", encoding="utf-8") as log:
        process = subprocess.Popen(
            [sys.executable, "-u", str(Path(__file__).resolve()), "--serve"],
            cwd=ROOT,
            env=environment,
            stdin=subprocess.PIPE,
            stdout=log,
            stderr=subprocess.STDOUT,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        evidence["pid"] = process.pid
        evidence["command"] = (
            "python plans/20261112-fastapi-backend/verify-http.py --serve"
        )
        try:
            with httpx.Client(
                base_url=f"http://127.0.0.1:{PORT}", timeout=10, trust_env=False
            ) as client:
                startup_started = time.monotonic()
                deadline = startup_started + 30
                while True:
                    if process.poll() is not None:
                        raise RuntimeError(
                            "Uvicorn exited before readiness; inspect server log"
                        )
                    try:
                        health = client.get("/api/v1/health")
                        if health.status_code == 200:
                            break
                    except httpx.ConnectError:
                        pass
                    if time.monotonic() >= deadline:
                        raise TimeoutError("Uvicorn readiness timeout")
                    time.sleep(0.1)
                evidence["statuses"]["health"] = health.status_code
                evidence["startup_seconds"] = time.monotonic() - startup_started
                assert health.json()["model_loaded"] is True
                for name, path in (
                    ("model", "/api/v1/model"),
                    ("clusters", "/api/v1/clusters"),
                    ("swagger", "/docs"),
                    ("openapi", "/openapi.json"),
                ):
                    response = client.get(path)
                    evidence["statuses"][name] = response.status_code
                    assert response.status_code == 200
                    if name in ("model", "clusters"):
                        assert response.json()["model_id"] == metadata["model_id"]
                single = client.post("/api/v1/predict", json=tracks[0])
                batch = client.post("/api/v1/predict/batch", json={"tracks": tracks})
                invalid = client.post("/api/v1/predict", json={})
                for name, response, expected in (
                    ("single", single, 200),
                    ("batch", batch, 200),
                    ("invalid", invalid, 422),
                ):
                    evidence["statuses"][name] = response.status_code
                    assert response.status_code == expected
                results = batch.json()["predictions"]
                labels = [result["cluster_id"] for result in results]
                np.testing.assert_array_equal(labels, sample["predictions"])
                np.testing.assert_allclose(
                    [r["distances"] for r in results],
                    sample["distances"],
                    rtol=1e-9,
                    atol=1e-7,
                )
                assert single.json()["cluster_id"] == sample["predictions"][0]
                np.testing.assert_allclose(
                    single.json()["distances"],
                    sample["distances"][0],
                    rtol=1e-9,
                    atol=1e-7,
                )
                evidence.update(
                    {
                        "status": "PASS",
                        "model_id": metadata["model_id"],
                        "verified_records": len(results),
                        "prediction_counts": {
                            str(label): labels.count(label) for label in (0, 1)
                        },
                        "single_result": {
                            key: single.json()[key]
                            for key in ("cluster_id", "distances")
                        },
                        "max_distance_absolute_error": float(
                            np.max(
                                np.abs(
                                    np.asarray([r["distances"] for r in results])
                                    - sample["distances"]
                                )
                            )
                        ),
                    }
                )
        finally:
            try:
                process.stdin.write("q")
                process.stdin.flush()
            except (BrokenPipeError, OSError):
                pass
            finally:
                process.stdin.close()
            try:
                evidence["server_exit_code"] = process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                process.terminate()
                process.wait(timeout=10)
                evidence["status"] = "FAIL"
                evidence["forced_termination"] = True
            with socket.socket() as probe:
                probe.settimeout(1)
                evidence["port_released"] = probe.connect_ex(("127.0.0.1", PORT)) != 0
            (REPORTS / "http-smoke.json").write_text(
                json.dumps(evidence, indent=2) + "\n"
            )
    assert evidence["server_exit_code"] == 0 and evidence["port_released"]
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    if sys.argv[1:] == ["--serve"]:
        serve()
    else:
        verify()
