"""Exercise real selection events across projections under hosted-style latency."""

import argparse
import importlib.util
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "refinement", ROOT / "plans/20261112-ui-refinement/verify-browser.py"
)
refinement = importlib.util.module_from_spec(spec)
spec.loader.exec_module(refinement)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:7872/")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    checks = []
    with sync_playwright() as p:
        browser = p.chromium.launch(
            args=[
                "--use-gl=angle",
                "--use-angle=swiftshader",
                "--enable-unsafe-swiftshader",
            ]
        )
        page = browser.new_page(viewport={"width": 768, "height": 1024})
        cdp = page.context.new_cdp_session(page)
        cdp.send("Network.enable")
        cdp.send(
            "Network.emulateNetworkConditions",
            {
                "offline": False,
                "latency": 500,
                "downloadThroughput": -1,
                "uploadThroughput": -1,
            },
        )
        refinement.ready(page, args.base)
        refinement.choose(page, "Cluster Explorer")
        for trial in range(5):
            refinement.mode(page, "3d")
            page.wait_for_function("""() => document.querySelector(
              '#explorer-space .js-plotly-plot').data[0].type === 'scatter3d'""")
            refinement.mode(page, "2d")
            page.wait_for_function("""() => document.querySelector(
              '#explorer-space .js-plotly-plot').data[0].type !== 'scatter3d'""")
            refinement.click_sample(page)
            checks.append({"trial": trial, "status": "PASS"})
            page.locator('#explorer-space [data-action="reset"]').click()
        browser.close()
    evidence = {"base": args.base, "latency_ms": 500, "checks": checks}
    args.output.write_text(json.dumps(evidence, indent=2))
    print(json.dumps(evidence))


if __name__ == "__main__":
    main()
