"""Owned live browser verification; public aggregate mode, no input logging."""

from __future__ import annotations

import json
import os
import re
import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORTS = Path(__file__).resolve().parent / "reports"
API_PORT = 8010
WEB_PORT = 7871

WEB_CODE = """
import sys
from spotify_cluster.web.app import create_app, launch_options
app = create_app()
app.launch(prevent_thread_lock=True, **launch_options())
try:
    sys.stdin.read(1)
finally:
    app.close()
"""


def port_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        return sock.connect_ex(("127.0.0.1", port)) != 0


def wait_port_free(port: int, timeout: float = 15.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if port_free(port):
            return True
        time.sleep(0.25)
    return port_free(port)


def wait_ready(process: subprocess.Popen, url: str, timeout: float = 60.0) -> None:
    import httpx

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError("Owned server exited before readiness")
        try:
            if httpx.get(url, timeout=2, trust_env=False).status_code == 200:
                return
        except httpx.HTTPError:
            pass
        time.sleep(0.2)
    raise TimeoutError("Owned server readiness timeout")


def start_api() -> subprocess.Popen:
    public = ROOT / "artifacts" / "visualization-public-v1"
    if not public.is_dir():
        raise RuntimeError(
            "Public visualization artifact required; prepare visualization-public-v1"
        )
    env = os.environ.copy()
    env.update(
        {
            "SPOTIFY_MODEL_DIR": str(ROOT / "artifacts" / "deployment-v1"),
            "SPOTIFY_VISUALIZATION_DIR": str(public),
            "SPOTIFY_PUBLIC_MODE": "1",
            "SPOTIFY_RESEARCH_DIR": str(ROOT / "artifacts" / "research-v1"),
        }
    )
    return subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "spotify_cluster.api.app:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(API_PORT),
        ],
        cwd=ROOT,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def start_web() -> subprocess.Popen:
    env = os.environ.copy()
    env.update(
        {
            "SPOTIFY_API_BASE_URL": f"http://127.0.0.1:{API_PORT}",
            "SPOTIFY_WEB_HOST": "127.0.0.1",
            "SPOTIFY_WEB_PORT": str(WEB_PORT),
            "GRADIO_ANALYTICS_ENABLED": "False",
        }
    )
    return subprocess.Popen(
        [sys.executable, "-c", WEB_CODE],
        cwd=ROOT,
        env=env,
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True,
    )


def stop(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return
    try:
        if process.stdin is not None:
            process.stdin.write("q")
            process.stdin.flush()
            process.stdin.close()
        process.wait(timeout=15)
    except (OSError, subprocess.TimeoutExpired):
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=10)


def browser_checks(base: str, screenshots: Path) -> dict:
    from playwright.sync_api import expect, sync_playwright

    screenshots.mkdir(parents=True, exist_ok=True)
    evidence = {
        "status": "PASS",
        "mode": "aggregate-public",
        "viewports": [],
        "screenshots": [],
        "checks": {},
        "errors": [],
    }
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            for width, height in ((1440, 900), (768, 1024), (375, 812)):
                page = browser.new_page(
                    viewport={"width": width, "height": height},
                    reduced_motion="no-preference",
                )
                page.on(
                    "pageerror",
                    lambda error: evidence["errors"].append(
                        "Browser runtime error: " + type(error).__name__
                    ),
                )
                page.on(
                    "console",
                    lambda message: evidence["errors"].append("Console error")
                    if message.type == "error"
                    else None,
                )
                page.goto(base, wait_until="load", timeout=60000)
                expect(page.get_by_text("API ready", exact=True).first).to_be_visible(
                    timeout=45000
                )
                expect(page.locator(".obs-hero h1")).to_be_visible()
                overflow = page.evaluate(
                    "() => ({doc: document.documentElement.scrollWidth,"
                    " win: window.innerWidth})"
                )
                assert overflow["doc"] <= overflow["win"] + 1, overflow
                expect(
                    page.locator("#overview-space .obs-plot svg").first
                ).to_be_visible(timeout=30000)
                expect(page.locator("#overview-space .obs-caption")).to_contain_text(
                    "Aggregate density"
                )
                evidence["viewports"].append(
                    {"width": width, "height": height, "overflow": overflow}
                )
                page.screenshot(
                    path=str(screenshots / f"{width}-overview.png"),
                    full_page=False,
                )
                evidence["screenshots"].append(f"{width}-overview.png")

                page.get_by_role("tab", name="Cluster Explorer").click()
                expect(page.locator("#explorer-space .obs-caption")).to_contain_text(
                    "Aggregate density", timeout=20000
                )
                expect(
                    page.get_by_role("button", name="PCA 2D", exact=True)
                ).to_be_disabled()
                expect(
                    page.get_by_role("button", name="Constellation", exact=True)
                ).to_be_disabled()
                table = page.locator("#feature-table")
                expect(table).to_be_visible()
                mean_text = table.inner_text()
                page.get_by_text("Median", exact=True).first.click()
                page.wait_for_timeout(500)
                assert table.inner_text() != mean_text
                evidence["checks"][f"explorer-{width}"] = "PASS"
                page.screenshot(
                    path=str(screenshots / f"{width}-explorer.png"),
                    full_page=False,
                )
                evidence["screenshots"].append(f"{width}-explorer.png")

                page.get_by_role("tab", name="Predict Cluster").click()
                result = page.locator("#prediction-result")
                loudness = page.get_by_label(re.compile("Loudness")).first
                loudness.fill("")
                page.get_by_role("button", name="Predict cluster", exact=True).click()
                expect(
                    result.get_by_text("finite number", exact=False).first
                ).to_be_visible(timeout=8000)
                expect(result.locator(".obs-prediction")).to_have_count(0)
                page.get_by_role(
                    "button", name="Load illustrative F9 vector", exact=True
                ).click()
                page.wait_for_timeout(900)
                page.get_by_role("button", name="Predict cluster", exact=True).click()
                expect(result.locator(".obs-prediction")).to_be_visible(timeout=15000)
                expect(result.get_by_text("NEAREST", exact=False).first).to_be_visible()
                expect(
                    result.get_by_text("not a probability", exact=False).first
                ).to_be_visible()
                evidence["checks"][f"predict-{width}"] = "PASS"
                page.screenshot(
                    path=str(screenshots / f"{width}-predict.png"),
                    full_page=False,
                )
                evidence["screenshots"].append(f"{width}-predict.png")

                page.get_by_role("tab", name="Research & Methodology").click()
                page.wait_for_timeout(500)
                page.evaluate("window.scrollTo(0, 0)")
                page.wait_for_timeout(300)
                expect(
                    page.get_by_text("What this partition", exact=False).first
                ).to_be_visible()
                page.get_by_text("Methodology and Reproducibility", exact=True).click()
                evidence_heading = page.get_by_text(
                    "Two identities, never one score", exact=False
                ).first
                evidence_heading.scroll_into_view_if_needed()
                expect(evidence_heading).to_be_visible()
                evidence["checks"][f"research-{width}"] = "PASS"
                page.screenshot(
                    path=str(screenshots / f"{width}-research.png"),
                    full_page=False,
                )
                evidence["screenshots"].append(f"{width}-research.png")
                page.close()

            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.goto(base, wait_until="load", timeout=60000)
            expect(page.get_by_text("API ready", exact=True).first).to_be_visible(
                timeout=45000
            )
            focus = []
            for _ in range(12):
                page.keyboard.press("Tab")
                focus.append(
                    page.evaluate(
                        "() => (document.activeElement.getAttribute('aria-label')"
                        " || document.activeElement.innerText || '').trim()"
                        ".slice(0, 40)"
                    )
                )
            assert any("cluster explorer" in item.lower() for item in focus), focus
            evidence["checks"]["keyboard"] = "PASS"
            page.locator('#overview-space button[data-view="density"]').focus()
            outline = page.locator(
                '#overview-space button[data-view="density"]'
            ).evaluate("b => getComputedStyle(b).outlineStyle")
            assert outline == "solid"
            evidence["checks"]["focus-outline"] = "PASS"
            page.close()

            reduced = browser.new_page(
                viewport={"width": 1440, "height": 900}, reduced_motion="reduce"
            )
            reduced.goto(base, wait_until="load", timeout=60000)
            expect(reduced.get_by_text("API ready", exact=True).first).to_be_visible(
                timeout=45000
            )
            transition = reduced.locator(".obs-card").first.evaluate(
                "e => getComputedStyle(e).transitionDuration"
            )
            assert float(transition.replace("s", "")) < 0.01, transition
            evidence["checks"]["reduced-motion"] = "PASS"
            reduced.close()
        finally:
            browser.close()
    return evidence


def main() -> int:
    REPORTS.mkdir(parents=True, exist_ok=True)
    if not (port_free(API_PORT) and port_free(WEB_PORT)):
        raise RuntimeError("Owned verification ports are already in use")
    api = start_api()
    web = start_web()
    try:
        wait_ready(api, f"http://127.0.0.1:{API_PORT}/api/v1/health")
        wait_ready(web, f"http://127.0.0.1:{WEB_PORT}/")
        evidence = browser_checks(
            f"http://127.0.0.1:{WEB_PORT}/",
            REPORTS / "screenshots",
        )
    finally:
        stop(web)
        stop(api)
        wait_port_free(API_PORT)
        wait_port_free(WEB_PORT)
    evidence["ports_released"] = {
        "api": port_free(API_PORT),
        "web": port_free(WEB_PORT),
    }
    evidence["private_features_logged"] = False
    (REPORTS / "browser.json").write_text(
        json.dumps(evidence, indent=2) + "\n", encoding="utf-8"
    )
    print(
        {
            "status": evidence["status"],
            "viewports": len(evidence["viewports"]),
            "errors": len(evidence["errors"]),
            "ports_released": evidence["ports_released"],
        }
    )
    return 0 if evidence["status"] == "PASS" and not evidence["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
