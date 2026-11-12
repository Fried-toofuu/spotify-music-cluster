"""Regression check for clipped slider inputs, accordion labels and PCA controls."""

import argparse
import json
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

REPORTS = Path(__file__).parent / "reports"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", default="after")
    args = parser.parse_args()
    shots = REPORTS / "points" / f"controls-{args.tag}"
    shots.mkdir(parents=True, exist_ok=True)
    evidence = {"checks": [], "errors": []}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            for width, height in [(1440, 900), (768, 1024), (375, 812)]:
                page = browser.new_page(viewport={"width": width, "height": height})
                page.goto("http://127.0.0.1:7860/", wait_until="domcontentloaded")
                expect(page.get_by_text("API ready", exact=True)).to_be_visible(
                    timeout=30000
                )
                page.get_by_role("tab", name="Predict Cluster", exact=True).click()
                inputs = page.locator('#predict-form input[type="number"]')
                expect(inputs).to_have_count(9)
                geometry = inputs.evaluate_all("""inputs => inputs.map(e => {
                  const r=e.getBoundingClientRect();
                  const p=e.parentElement.getBoundingClientRect();
                  return {height:r.height, parentHeight:p.height,
                    clipped:r.top < p.top-1 || r.bottom > p.bottom+1};
                })""")
                for item in geometry:
                    if item["clipped"]:
                        evidence["errors"].append(f"{width}: input clipped {item}")
                # Editing the formerly clipped field must still submit real inference.
                inputs.nth(0).fill("0.42")
                page.get_by_role("button", name="Predict cluster", exact=True).click()
                expect(
                    page.locator("#prediction-result .obs-prediction")
                ).to_be_visible(timeout=30000)
                label = page.locator("#distance-breakdown > .label-wrap")
                label.scroll_into_view_if_needed()
                inset = label.evaluate("""e => {
                  const r=e.getBoundingClientRect();
                  const t=e.firstElementChild.getBoundingClientRect();
                  const parent=getComputedStyle(e.parentElement);
                  return {left:t.left-r.left, height:r.height,
                    outerRadius:parent.borderTopLeftRadius,
                    innerRadius:getComputedStyle(e).borderTopLeftRadius};
                }""")
                if inset["left"] < 12:
                    evidence["errors"].append(f"{width}: accordion text lacks inset")
                label.click()
                expect(
                    page.locator("#distance-breakdown .js-plotly-plot")
                ).to_be_visible()
                page.screenshot(
                    path=str(shots / f"{width}-prediction.png"), full_page=True
                )
                for tab, host in [
                    ("Overview", "overview-space"),
                    ("Cluster Explorer", "explorer-space"),
                ]:
                    page.get_by_role("tab", name=tab, exact=True).click()
                    group = page.locator(f"#{host} .obs-seg")
                    buttons = group.locator("button:visible")
                    boxes = buttons.evaluate_all("""buttons => buttons.map(e => {
                      const r=e.getBoundingClientRect(), s=getComputedStyle(e);
                      return {width:r.width,height:r.height,margin:s.margin};
                    })""")
                    if (
                        max(b["width"] for b in boxes) - min(b["width"] for b in boxes)
                        > 1
                    ):
                        evidence["errors"].append(f"{width} {host}: unequal PCA widths")
                    if any(b["height"] < 44 or b["margin"] != "0px" for b in boxes):
                        evidence["errors"].append(
                            f"{width} {host}: PCA target/margin mismatch"
                        )
                    page.screenshot(
                        path=str(shots / f"{width}-{host}.png"), full_page=True
                    )
                page.get_by_text("Detailed aggregate statistics", exact=True).click()
                expect(
                    page.get_by_text("Raw-unit aggregate statistics", exact=True)
                ).to_be_visible()
                if page.evaluate("document.documentElement.scrollWidth > innerWidth+1"):
                    evidence["errors"].append(f"{width}: page overflow")
                evidence["checks"].append(
                    {"width": width, "inputs": geometry, "accordion": inset}
                )
                page.close()
        finally:
            browser.close()
    (REPORTS / f"control-layout-{args.tag}.json").write_text(
        json.dumps(evidence, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {"viewports": len(evidence["checks"]), "errors": evidence["errors"]},
            indent=2,
        )
    )
    assert not evidence["errors"]


if __name__ == "__main__":
    main()
