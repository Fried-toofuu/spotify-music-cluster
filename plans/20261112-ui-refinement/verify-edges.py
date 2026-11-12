"""Check reflow, touch scroll escape and honest offline states in Chromium."""

import json
import os
import socket
import subprocess
import sys
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

HERE = Path(__file__).parent
ROOT = HERE.parents[1]


def free(port):
    with socket.socket() as sock:
        return sock.connect_ex(("127.0.0.1", port)) != 0


def main():
    evidence = {"reflow": [], "offline": False, "touch_scroll": False}
    with sync_playwright() as p:
        browser = p.chromium.launch(
            args=[
                "--use-gl=angle",
                "--use-angle=swiftshader",
                "--enable-unsafe-swiftshader",
            ]
        )
        page = browser.new_page()
        page.goto("http://127.0.0.1:7872/", wait_until="domcontentloaded")
        expect(page.locator("#overview-space .js-plotly-plot")).to_be_visible(
            timeout=60000
        )
        for width, height in [(320, 640), (480, 640), (1024, 768), (812, 375)]:
            page.set_viewport_size({"width": width, "height": height})
            for name in [
                "Overview",
                "Cluster Explorer",
                "Predict Cluster",
                "Research & Methodology",
            ]:
                page.get_by_role("tab", name=name, exact=True).click()
                assert not page.evaluate(
                    "document.documentElement.scrollWidth>innerWidth+1"
                ), (width, name)
            evidence["reflow"].append([width, height])
        page.set_viewport_size({"width": 768, "height": 1024})
        page.evaluate("document.documentElement.style.fontSize='20px'")
        page.get_by_role("tab", name="Overview", exact=True).click()
        assert not page.evaluate("document.documentElement.scrollWidth>innerWidth+1")
        evidence["125-percent-root-text"] = True
        page.close()
        # No WebGL is required to verify normal touch scrolling over the 2D preview.
        page = browser.new_page(
            viewport={"width": 375, "height": 640}, has_touch=True, is_mobile=True
        )
        page.goto("http://127.0.0.1:7872/", wait_until="domcontentloaded")
        plot = page.locator("#overview-space .js-plotly-plot")
        expect(plot).to_be_visible(timeout=60000)
        plot.scroll_into_view_if_needed()
        box = plot.bounding_box()
        before = page.evaluate("scrollY")
        cdp = page.context.new_cdp_session(page)
        x, y = box["x"] + box["width"] * 0.7, box["y"] + 200
        cdp.send(
            "Input.dispatchTouchEvent",
            {"type": "touchStart", "touchPoints": [{"x": x, "y": y}]},
        )
        for step in range(1, 9):
            cdp.send(
                "Input.dispatchTouchEvent",
                {"type": "touchMove", "touchPoints": [{"x": x, "y": y - step * 15}]},
            )
        cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
        page.wait_for_timeout(300)
        evidence["touch_scroll"] = page.evaluate("scrollY") > before
        page.close()
        page = browser.new_page(
            viewport={"width": 375, "height": 640}, has_touch=True, is_mobile=True
        )
        page.goto("http://127.0.0.1:7872/", wait_until="domcontentloaded")
        expect(page.locator("#overview-space .js-plotly-plot")).to_be_visible(
            timeout=60000
        )
        cdp = page.context.new_cdp_session(page)
        page.get_by_role("tab", name="Cluster Explorer", exact=True).click()
        page.locator('#explorer-space [data-view="3d"]').click()
        plot = page.locator("#explorer-space .js-plotly-plot")
        plot.scroll_into_view_if_needed()
        page.wait_for_function(
            "document.querySelector('#explorer-space .js-plotly-plot')"
            "._fullLayout.scene?._scene"
        )
        toggle = page.locator('#explorer-space [data-action="touch"]')
        toggle.tap()
        expect(toggle).to_have_text("Resume page scrolling")
        plot.scroll_into_view_if_needed()
        page.evaluate(
            "() => new Promise(resolve => requestAnimationFrame("
            "() => requestAnimationFrame(resolve)))"
        )
        camera = plot.evaluate(
            "g=>JSON.stringify(g._fullLayout.scene._scene.getCamera())"
        )
        box = plot.bounding_box()
        before_scroll = page.evaluate("scrollY")
        x, y = box["x"] + box["width"] * 0.6, box["y"] + box["height"] * 0.6
        cdp.send(
            "Input.dispatchTouchEvent",
            {"type": "touchStart", "touchPoints": [{"x": x, "y": y}]},
        )
        for step in range(1, 9):
            cdp.send(
                "Input.dispatchTouchEvent",
                {
                    "type": "touchMove",
                    "touchPoints": [{"x": x - step * 5, "y": y - step * 10}],
                },
            )
            page.evaluate("() => new Promise(requestAnimationFrame)")
        cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
        page.wait_for_timeout(300)
        evidence["touch_3d_rotation"] = camera != plot.evaluate(
            "g=>JSON.stringify(g._fullLayout.scene._scene.getCamera())"
        )
        evidence["rotation_did_not_scroll_page"] = (
            page.evaluate("scrollY") == before_scroll
        )
        toggle.tap()
        expect(toggle).to_have_text("Enable rotation")
        page.close()
        browser.close()
    if not (free(7873) and free(8019)):
        raise RuntimeError("Offline check ports already have owners")
    env = {
        **os.environ,
        "SPOTIFY_WEB_PORT": "7873",
        "GRADIO_ANALYTICS_ENABLED": "False",
    }
    code = """
import sys
from spotify_cluster.web.app import create_app, launch_options
from spotify_cluster.web.api_client import APIClient
app = create_app(APIClient(base_url='http://127.0.0.1:8019'))
app.launch(prevent_thread_lock=True, **launch_options())
try:
    sys.stdin.read(1)
finally:
    app.close()
"""
    server = subprocess.Popen(
        [sys.executable, "-c", code],
        cwd=ROOT,
        env=env,
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        import time

        import httpx

        deadline = time.monotonic() + 45
        while time.monotonic() < deadline:
            if server.poll() is not None:
                raise RuntimeError(server.stderr.read())
            try:
                if (
                    httpx.get("http://127.0.0.1:7873/", trust_env=False).status_code
                    == 200
                ):
                    break
            except httpx.HTTPError:
                pass
            time.sleep(0.2)
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 375, "height": 812})
            page.goto("http://127.0.0.1:7873/", wait_until="domcontentloaded")
            expect(page.get_by_text("API unavailable", exact=True)).to_be_visible(
                timeout=30000
            )
            page.screenshot(
                path=str(HERE / "reports/aggregate/offline-375.png"), full_page=True
            )
            page.get_by_role("tab", name="Predict Cluster", exact=True).click()
            page.get_by_role("button", name="Predict cluster", exact=True).click()
            expect(page.locator("#prediction-result")).to_contain_text(
                "Could not complete"
            )
            expect(page.locator("#prediction-result .obs-prediction")).to_have_count(0)
            evidence["offline"] = True
            browser.close()
    finally:
        if server.poll() is None:
            server.stdin.write("\n")
            server.stdin.flush()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.terminate()
            server.wait(timeout=10)
    evidence["offline_port_released"] = free(7873)
    (HERE / "reports/edges.json").write_text(
        json.dumps(evidence, indent=2), encoding="utf-8"
    )
    print(json.dumps(evidence, indent=2))
    assert all(
        [
            evidence["offline"],
            evidence["touch_scroll"],
            evidence["offline_port_released"],
            evidence["touch_3d_rotation"],
            evidence["rotation_did_not_scroll_page"],
        ]
    )


if __name__ == "__main__":
    main()
