"""Real-browser permanent-light checks; points screenshots remain local/ignored."""

import importlib.util
import json
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).parent / "reports" / "points"
spec = importlib.util.spec_from_file_location(
    "refinement", ROOT / "plans/20261112-ui-refinement/verify-browser.py"
)
refinement = importlib.util.module_from_spec(spec)
spec.loader.exec_module(refinement)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    evidence = {
        "checks": {},
        "errors": [],
        "console_errors": [],
        "navigation_console_errors": [],
        "failed_requests": [],
        "responses": [],
    }
    with sync_playwright() as p:
        browser = p.chromium.launch(
            args=[
                "--use-gl=angle",
                "--use-angle=swiftshader",
                "--enable-unsafe-swiftshader",
            ]
        )
        for width, height in [(1440, 900), (768, 1024), (375, 812)]:
            page = browser.new_page(
                viewport={"width": width, "height": height}, color_scheme="dark"
            )
            phase = {"navigation": False}

            def console_message(message, phase=phase):
                if message.type != "error":
                    return
                # Gradio closes its SSE client on reload and logs the abort.
                # Keep these receipts, separate from errors during interaction.
                key = (
                    "navigation_console_errors"
                    if phase["navigation"]
                    and (
                        "AbortError" in message.text
                        or "Unexpected error Connection errored out" in message.text
                    )
                    else "console_errors"
                )
                evidence[key].append(message.text)

            page.on("pageerror", lambda error: evidence["errors"].append(str(error)))
            page.on("console", console_message)
            page.on(
                "requestfailed",
                lambda r: evidence["failed_requests"].append(
                    {"path": r.url.split("?")[0].split("/")[-1], "reason": r.failure}
                ),
            )
            page.on(
                "response",
                lambda r: evidence["responses"].append(
                    {"status": r.status, "path": r.url.split("?")[0].split("/")[-1]}
                )
                if r.status >= 400
                else None,
            )
            refinement.ready(page, "http://127.0.0.1:7872/?__theme=dark")
            for name, slug in [
                ("Overview", "overview"),
                ("Cluster Explorer", "explorer"),
                ("Predict Cluster", "predict"),
                ("Research & Methodology", "research"),
            ]:
                refinement.choose(page, name)
                expect(page.locator("body")).not_to_have_class("dark")
                assert (
                    page.evaluate("getComputedStyle(document.body).backgroundColor")
                    == "rgb(247, 249, 252)"
                )
                assert not page.evaluate(
                    "document.documentElement.scrollWidth > innerWidth + 1"
                )
                assert page.locator("button").filter(has_text="Dark mode").count() == 0
                page.screenshot(
                    path=str(OUT / f"{width}-dark-preference-{slug}.png"),
                    full_page=True,
                    animations="disabled",
                )
                evidence["checks"][f"{width}-{slug}-dark-preference-light"] = "PASS"
            refinement.choose(page, "Cluster Explorer")
            host = page.locator("#explorer-space")
            for mode in ["2d", "3d", "density", "constellation"]:
                host.locator(f'[data-view="{mode}"]').click()
                if mode == "constellation":
                    expect(
                        host.locator("canvas.obs-constellation-canvas")
                    ).to_be_visible(timeout=30000)
                else:
                    page.wait_for_function(
                        """mode => {
                      const host = document.querySelector('#explorer-space');
                      const p = host.querySelector('.js-plotly-plot');
                      return p && p.layout && p.layout.paper_bgcolor === '#FFFFFF' &&
                        (mode === '3d' ? p.data[0].type === 'scatter3d'
                          && p.layout.scene.bgcolor === '#FFFFFF'
                         : mode === 'density' ? p.data[0].type === 'heatmap'
                         : p.data[0].type.startsWith('scatter'));
                    }""",
                        arg=mode,
                    )
                page.screenshot(
                    path=str(OUT / f"{width}-light-{mode}.png"),
                    full_page=True,
                    animations="disabled",
                )
                evidence["checks"][f"{width}-{mode}-light"] = "PASS"
            page.get_by_role("button", name="Refresh live data", exact=True).click()
            expect(page.locator("#api-status")).to_contain_text("API ready")
            page.emulate_media(color_scheme="light")
            page.emulate_media(color_scheme="dark")
            phase["navigation"] = True
            page.reload()
            expect(page.locator("#api-status")).to_contain_text(
                "API ready", timeout=30000
            )
            assert (
                page.evaluate("getComputedStyle(document.body).backgroundColor")
                == "rgb(247, 249, 252)"
            )
            evidence["checks"][f"{width}-refresh-reload-preference-change"] = "PASS"
            page.close()
        browser.close()
    (OUT.parent / "light-browser.json").write_text(json.dumps(evidence, indent=2))
    assert not evidence["errors"], evidence["errors"]
    assert not evidence["console_errors"], evidence["console_errors"]
    assert not evidence["responses"], evidence["responses"]
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
