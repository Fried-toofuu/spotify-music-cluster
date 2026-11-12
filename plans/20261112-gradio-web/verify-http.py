"""Owned real servers/browser smoke; no fitting or raw input logging."""

import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORTS = Path(__file__).resolve().parent / "reports"


def serve_web():
    from spotify_cluster.web.app import create_app, launch_options

    app = create_app()
    app.launch(prevent_thread_lock=True, **launch_options())
    try:
        sys.stdin.read(1)
    finally:
        app.close()


def wait_ready(process, url):
    import httpx

    deadline = time.monotonic() + 45
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError("Server exited; inspect sanitized server log")
        try:
            if httpx.get(url, timeout=2, trust_env=False).status_code == 200:
                return
        except httpx.HTTPError:
            pass
        time.sleep(0.15)
    raise TimeoutError("Local server readiness timeout")


def stop(process):
    if process.poll() is None:
        try:
            process.stdin.write("q")
            process.stdin.flush()
        except (BrokenPipeError, OSError):
            pass
        finally:
            process.stdin.close()
        try:
            process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            process.terminate()
            process.wait(timeout=10)
            raise RuntimeError("Server required forced termination") from None
    assert process.returncode == 0


def chart_source(page):
    return page.locator("#feature-comparison img").get_attribute("src")


def wait_chart_change(page, previous):
    for _ in range(60):
        current = chart_source(page)
        if current and current != previous:
            return current
        page.wait_for_timeout(100)
    raise AssertionError("Comparison chart did not refresh")


def browser_check():
    from playwright.sync_api import expect, sync_playwright

    screenshots = REPORTS / "screenshots"
    screenshots.mkdir(exist_ok=True)
    evidence = {"viewports": [], "screenshots": [], "errors": []}
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        try:
            for width, height in ((1440, 900), (768, 1024), (375, 812)):
                page = browser.new_page(
                    viewport={"width": width, "height": height}, color_scheme="dark"
                )
                page.on(
                    "pageerror",
                    lambda _: evidence["errors"].append("Browser runtime error"),
                )
                page.goto("http://127.0.0.1:7860")
                expect(
                    page.get_by_text("Live verified aggregates loaded.", exact=False)
                ).to_be_visible()
                expect(page.locator(".metric").first).to_contain_text("89,741")
                expect(
                    page.get_by_role("heading", name="97.302%", exact=False)
                ).to_be_visible()
                for tab in (
                    "Overview",
                    "Predict Cluster",
                    "Cluster Explorer",
                    "Research & Methodology",
                ):
                    page.get_by_role("tab", name=tab, exact=True).click()
                    if tab == "Predict Cluster":
                        loudness = page.get_by_label("Loudness (dB)", exact=True)
                        loudness.fill("")
                        page.get_by_role(
                            "button", name="Predict Cluster", exact=True
                        ).click()
                        expect(
                            page.get_by_text(
                                "Loudness must be a finite number.", exact=True
                            )
                        ).to_be_visible()
                        expect(page.locator(".translucent:visible")).to_have_count(0)
                        page.screenshot(
                            path=str(screenshots / f"{width}-invalid-input.png"),
                            full_page=True,
                        )
                        page.get_by_text(
                            "Load synthetic F9 example", exact=True
                        ).click()
                        page.get_by_role(
                            "button", name="Predict Cluster", exact=True
                        ).click()
                        expect(
                            page.get_by_text(
                                "Prediction received from the API.", exact=True
                            )
                        ).to_be_visible()
                        expect(
                            page.get_by_text(
                                "Historical equivalence: NOT VERIFIED.", exact=True
                            )
                        ).to_be_visible()
                    if tab == "Cluster Explorer":
                        expect(
                            page.get_by_text(
                                "In this model, Cluster 1 has higher", exact=False
                            )
                        ).to_be_visible()
                        table = page.locator("#feature-table")
                        mean_text = table.inner_text()
                        chart = chart_source(page)
                        page.get_by_text("Median", exact=True).click()
                        chart = wait_chart_change(page, chart)
                        assert table.inner_text() != mean_text
                        assert "Instrumentalness" in table.inner_text()
                        feature_input = page.get_by_label(
                            "Acoustic feature", exact=True
                        )
                        feature_input.fill("Tempo")
                        page.get_by_role("option", name="Tempo", exact=True).click()
                        chart = wait_chart_change(page, chart)
                        assert "Tempo" in table.inner_text()
                        assert "BPM" in table.inner_text()
                        cluster_input = page.get_by_label(
                            "Cluster selection", exact=True
                        )
                        cluster_input.fill("Cluster 1")
                        page.get_by_role("option", name="Cluster 1", exact=True).click()
                        expect(cluster_input).to_have_value("Cluster 1")
                        expect(
                            table.get_by_text("Cluster 0", exact=True)
                        ).to_have_count(0)
                        expect(
                            page.get_by_text("Cluster 1 ·", exact=False).first
                        ).to_be_visible()
                        wait_chart_change(page, chart)
                    expect(page.locator(".translucent:visible")).to_have_count(0)
                    expect(page.locator('[role="listbox"]:visible')).to_have_count(0)
                    overflow = page.evaluate(
                        "document.documentElement.scrollWidth > innerWidth"
                    )
                    slug = tab.lower().replace(" & ", "-").replace(" ", "-")
                    path = screenshots / f"{width}-{slug}.png"
                    page.screenshot(path=str(path), full_page=True)
                    evidence["screenshots"].append(path.name)
                    if overflow:
                        offenders = page.evaluate("""() =>
                            [...document.querySelectorAll('body *')]
                            .filter(e => e.getBoundingClientRect().right
                                > innerWidth + 2)
                            .slice(-20).map(e => [e.tagName,
                                e.getBoundingClientRect().width])""")
                        print("Overflow elements", offenders)
                    assert not overflow, f"Page overflow at {width}px in {tab}"
                evidence["viewports"].append([width, height])
                page.close()
        finally:
            browser.close()
    assert not evidence["errors"]
    return evidence


def verify():
    import httpx
    import numpy as np
    from gradio_client import Client

    from spotify_cluster.config import F9
    from spotify_cluster.web.api_client import APIClient
    from spotify_cluster.web.components import Handlers

    REPORTS.mkdir(exist_ok=True)
    for port in (8000, 7860):
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", port))
    processes, logs = [], []
    evidence = {"status": "FAIL", "worktree": str(ROOT), "processes": []}
    try:
        for name, script, flag, port, endpoint in (
            (
                "backend",
                ROOT / "plans/20261112-fastapi-backend/verify-http.py",
                "--serve",
                8000,
                "/api/v1/health",
            ),
            ("frontend", Path(__file__).resolve(), "--serve-web", 7860, "/"),
        ):
            log = (REPORTS / f"{name}-server.txt").open("w", encoding="utf-8")
            logs.append(log)
            command = [sys.executable, "-u", str(script), flag]
            process = subprocess.Popen(
                command,
                cwd=ROOT,
                stdin=subprocess.PIPE,
                stdout=log,
                stderr=subprocess.STDOUT,
                text=True,
                env={
                    **os.environ,
                    "SPOTIFY_MODEL_DIR": str(ROOT / "artifacts/deployment-v1"),
                    "SPOTIFY_API_BASE_URL": "http://127.0.0.1:8000",
                    "GRADIO_ANALYTICS_ENABLED": "False",
                },
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            processes.append(process)
            evidence["processes"].append(
                {
                    "name": name,
                    "pid": process.pid,
                    "port": port,
                    "command": " ".join(command),
                }
            )
            wait_ready(process, f"http://127.0.0.1:{port}{endpoint}")
        client = APIClient()
        handlers = Handlers(client)
        state, status, summary, distribution_chart, distribution, *_ = (
            handlers.refresh()
        )
        assert state is not None and "89,741" in summary
        assert distribution.Tracks.tolist() == [72211, 17530]
        assert [
            p.get_width() for p in distribution_chart.axes[0].patches
        ] == distribution.Tracks.tolist()
        model_id = state["model"]["model_id"]
        # Private sample remains only in memory. Neither raw features nor results
        # from private sample rows are included in the evidence output.
        sample = json.loads(
            (ROOT / "artifacts/deployment-v1/verification_sample.json").read_text()
        )
        values = sample["raw_f9"][0]
        direct = client.predict(dict(zip(F9, values, strict=True)))
        feedback, text, distance_chart, distances = handlers.predict(state, *values)
        assert "received" in feedback and model_id in text
        np.testing.assert_allclose(
            distances.Distance, direct["distances"], rtol=1e-9, atol=1e-7
        )
        np.testing.assert_allclose(
            [p.get_height() for p in distance_chart.axes[0].patches],
            direct["distances"],
            rtol=1e-9,
            atol=1e-7,
        )
        np.testing.assert_allclose(
            distances.Distance, sample["distances"][0], rtol=1e-9, atol=1e-7
        )
        assert f"Cluster {direct['cluster_id']}" in text
        assert direct["cluster_id"] == sample["predictions"][0]
        assert "nine" in handlers.predict(state, 0.5)[0]
        frontend = Client("http://127.0.0.1:7860", verbose=False)
        # Publicly labelled synthetic example, through the live Gradio HTTP event.
        synthetic = [0.72, 0.61, 0.38, 0.44, 118.5, -9.2, 0.05, 0.81, 0.13]
        result = frontend.predict(*synthetic, api_name="/predict_cluster")
        expected = client.predict(dict(zip(F9, synthetic, strict=True)))
        assert (
            "received" in result[0] and f"Cluster {expected['cluster_id']}" in result[1]
        )
        np.testing.assert_allclose(
            [r[1] for r in result[3]["data"]], expected["distances"]
        )
        evidence.update(
            model_id=model_id,
            training_count=89741,
            cluster_counts=distribution.Tracks.tolist(),
            private_sample_agreement=True,
            gradio_http_prediction=True,
        )
        if "--browser" in sys.argv:
            evidence["browser"] = browser_check()
            # Run the frontend skill's diagnostics, with its owned browser cleanup.
            checker = Path(
                "C:/Users/PC/.agents/skills/ak-frontend-design/scripts/render-check.mjs"
            )
            if checker.exists():
                result = subprocess.run(
                    [
                        "node",
                        str(checker),
                        "http://127.0.0.1:7860",
                        "--out",
                        str(REPORTS / "render-check"),
                    ],
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                (REPORTS / "render-check.txt").write_text(
                    result.stdout + result.stderr, encoding="utf-8"
                )
                evidence["render_check_exit"] = result.returncode
        # Confirm file-serving rejection without logging or reading private bodies.
        with httpx.Client(trust_env=False) as http:
            for path in (
                ROOT / "dataset.csv",
                ROOT / "artifacts/deployment-v1/model_bundle.joblib",
                ROOT / "Spotify_Music_Clustering_Final.ipynb",
            ):
                response = http.get(
                    "http://127.0.0.1:7860/gradio_api/file=" + path.as_posix()
                )
                assert response.status_code in (403, 404)
        stop(processes[0])
        assert "Cannot connect" in handlers.refresh()[1]
        assert "Cannot connect" in handlers.predict(None, *synthetic)[0]
        result = frontend.predict(*synthetic, api_name="/predict_cluster")
        assert "Cannot connect" in result[0] and result[1] == "No prediction available."
        evidence["offline_feedback"] = True
        evidence["status"] = "PASS"
    finally:
        for process in reversed(processes):
            stop(process)
        for log in logs:
            log.close()
        evidence["exit_codes"] = [p.returncode for p in processes]
        evidence["ports_released"] = {}
        for port in (8000, 7860):
            with socket.socket() as probe:
                evidence["ports_released"][str(port)] = (
                    probe.connect_ex(("127.0.0.1", port)) != 0
                )
        name = (
            "http-smoke-browser.json" if "--browser" in sys.argv else "http-smoke.json"
        )
        (REPORTS / name).write_text(json.dumps(evidence, indent=2) + "\n")
    assert all(evidence["ports_released"].values())
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    if "--serve-web" in sys.argv:
        serve_web()
    else:
        verify()
