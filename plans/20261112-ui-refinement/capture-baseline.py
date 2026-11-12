# ruff: noqa: E501  (browser expressions)
"""Read-only browser capture of existing services; no scientific data is logged."""

import json
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).parent
REPORTS = ROOT / "reports"


def main():
    shots = REPORTS / "baseline"
    shots.mkdir(parents=True, exist_ok=True)
    evidence = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(
            args=[
                "--use-gl=angle",
                "--use-angle=swiftshader",
                "--enable-unsafe-swiftshader",
            ]
        )
        for width, height in [(1440, 900), (768, 1024), (375, 812)]:
            page = browser.new_page(viewport={"width": width, "height": height})
            errors = []
            page.on("pageerror", lambda error, errors=errors: errors.append(str(error)))
            page.goto("http://127.0.0.1:7860/", wait_until="domcontentloaded")
            page.locator("#overview-space .js-plotly-plot").wait_for(timeout=60000)
            for tab in [
                "Overview",
                "Cluster Explorer",
                "Predict Cluster",
                "Research & Methodology",
            ]:
                page.get_by_role("tab", name=tab, exact=True).click()
                page.wait_for_timeout(800)
                page.evaluate("window.scrollTo(0,0)")
                slug = tab.split()[0].lower()
                page.screenshot(path=str(shots / f"{width}-{slug}.png"), full_page=True)
            page.get_by_role("tab", name="Overview", exact=True).click()
            evidence[str(width)] = page.locator("#overview-space").evaluate(
                "e => ({mapTop:e.getBoundingClientRect().top,overflow:document.documentElement.scrollWidth>innerWidth})"
            )
            evidence[str(width)]["errors"] = errors
            page.close()
        page = browser.new_page()
        try:
            response = page.goto(
                "https://acoustic-observatory.onrender.com/", timeout=90000
            )
            evidence["public"] = {"status": response.status, "title": page.title()}
        except Exception as exc:
            evidence["public"] = {"error": type(exc).__name__}
        browser.close()
    (REPORTS / "baseline.json").write_text(
        json.dumps(evidence, indent=2), encoding="utf-8"
    )
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
