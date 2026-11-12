# ruff: noqa: E501  (browser expressions)
"""Actual Chromium interactions against existing trusted HTTP services.

Points screenshots remain ignored; no feature rows or coordinates enter reports.
Pass --base for baseline regression checks or aggregate screenshot collection.
"""

import argparse
import json
import time
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).parent
REPORTS = ROOT / "reports"


def ready(page, base):
    start = time.monotonic()
    page.goto(base, wait_until="domcontentloaded", timeout=60000)
    expect(page.locator("#overview-space .js-plotly-plot")).to_be_visible(timeout=60000)
    page.wait_for_function(
        "document.querySelector('#overview-space .js-plotly-plot')?.data?.length > 0"
    )
    return round(time.monotonic() - start, 3)


def choose(page, name):
    page.get_by_role("tab", name=name, exact=True).click()


def mode(page, value):
    page.locator(f'#explorer-space [data-view="{value}"]').click()
    expect(page.locator(f'#explorer-space [data-view="{value}"]')).to_have_attribute(
        "aria-pressed", "true"
    )


def click_sample(page, *, touch=False):
    plot = page.locator("#explorer-space .js-plotly-plot")
    plot.scroll_into_view_if_needed()
    page.evaluate(
        "() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))"
    )
    # Choose a separated displayed data mark; mouse interaction invokes Plotly's real picking.
    point = plot.evaluate("""g => {
      const t=g.data[0], i=t.y.indexOf(Math.max(...t.y));
      return {x:g._fullLayout.xaxis.l2p(t.x[i])+g._fullLayout.xaxis._offset,
        y:g._fullLayout.yaxis.l2p(t.y[i])+g._fullLayout.yaxis._offset};
    }""")
    box = plot.bounding_box()
    if touch:
        page.touchscreen.tap(box["x"] + point["x"], box["y"] + point["y"])
    else:
        page.mouse.move(box["x"] + point["x"], box["y"] + point["y"])
        expect(page.locator("#explorer-space .hoverlayer")).to_contain_text(
            "Sample", timeout=10000
        )
        page.mouse.click(box["x"] + point["x"], box["y"] + point["y"])
    expect(page.locator("#explorer-detail .obs-selected-track")).to_be_visible(
        timeout=20000
    )
    expect(page.locator("#explorer-detail")).to_contain_text("Nearest sampled tracks")


def run(base, out, interactions=True, only_width=None):
    out.mkdir(parents=True, exist_ok=True)
    evidence = {
        "base": base,
        "checks": {},
        "viewports": [],
        "errors": [],
        "failed_requests": [],
    }
    check = evidence["checks"]
    with sync_playwright() as p:
        browser = p.chromium.launch(
            args=[
                "--use-gl=angle",
                "--use-angle=swiftshader",
                "--enable-unsafe-swiftshader",
            ]
        )
        for width, height in [(1440, 900), (768, 1024), (375, 812)]:
            if only_width and width != only_width:
                continue
            page = browser.new_page(
                viewport={"width": width, "height": height},
                has_touch=width == 375,
                is_mobile=width == 375,
            )
            page.on("pageerror", lambda error: evidence["errors"].append(str(error)))
            page.on(
                "requestfailed",
                lambda request: evidence["failed_requests"].append(
                    {
                        "path": request.url.split("?")[0].split("/")[-1],
                        "reason": request.failure,
                    }
                ),
            )
            elapsed = ready(page, base)
            page.screenshot(path=str(out / f"{width}-overview.png"), full_page=True)
            page.screenshot(path=str(out / f"{width}-overview-viewport.png"))
            box = page.locator("#overview-space").bounding_box()
            evidence["viewports"].append(
                {
                    "width": width,
                    "height": height,
                    "map_top": round(box["y"], 1),
                    "ready_seconds": elapsed,
                }
            )
            if interactions:
                assert box["y"] < (350 if width == 1440 else 700), box
            for tab, slug in [
                ("Cluster Explorer", "explorer"),
                ("Predict Cluster", "predict-empty"),
                ("Research & Methodology", "research"),
            ]:
                choose(page, tab)
                if slug == "explorer":
                    expect(
                        page.locator("#explorer-space .js-plotly-plot")
                    ).to_be_visible()
                if slug == "research":
                    expect(
                        page.get_by_text("What this partition", exact=False)
                    ).to_be_visible()
                page.evaluate("scrollTo(0,0)")
                page.screenshot(path=str(out / f"{width}-{slug}.png"), full_page=True)
                assert not page.evaluate(
                    "document.documentElement.scrollWidth>innerWidth+1"
                ), (width, tab)
            check[f"four-tabs-no-overflow-{width}"] = "PASS"
            if not interactions:
                page.close()
                continue
            choose(page, "Predict Cluster")
            expect(
                page.locator("#distance-breakdown .js-plotly-plot")
            ).not_to_be_visible()
            page.get_by_role("button", name="Predict cluster", exact=True).focus()
            page.keyboard.press("Enter")
            expect(page.locator("#prediction-result .obs-prediction")).to_be_visible(
                timeout=30000
            )
            expect(page.locator("#prediction-result")).to_contain_text(
                "not a probability"
            )
            page.locator("#distance-breakdown").get_by_text(
                "Distance Breakdown", exact=True
            ).click()
            expect(page.locator("#distance-breakdown .js-plotly-plot")).to_be_visible()
            page.screenshot(
                path=str(out / f"{width}-prediction-result.png"), full_page=True
            )
            # The label includes BPM; use the semantic spinbutton within its owning field.
            tempo = page.get_by_role("spinbutton", name="Tempo", exact=False)
            tempo.fill("")
            page.get_by_role("button", name="Predict cluster", exact=True).click()
            expect(page.locator("#prediction-result .obs-prediction")).to_have_count(
                0, timeout=20000
            )
            expect(page.locator("#prediction-result")).to_contain_text(
                "Could not complete"
            )
            page.screenshot(
                path=str(out / f"{width}-prediction-error.png"), full_page=True
            )
            page.get_by_role(
                "button", name="Load illustrative F9 vector", exact=True
            ).click()
            expect(page.locator("#prediction-result")).to_contain_text("Awaiting")
            page.get_by_role("button", name="Predict cluster", exact=True).click()
            expect(page.locator("#prediction-result .obs-prediction")).to_be_visible(
                timeout=30000
            )
            check[f"prediction-keyboard-exact-error-recovery-{width}"] = "PASS"
            choose(page, "Research & Methodology")
            expect(
                page.get_by_role("heading", name="Research Findings", exact=True)
            ).to_be_visible()
            method = page.locator(".obs-research-layer").filter(
                has=page.get_by_text("Methodology and Reproducibility", exact=True)
            )
            expect(method).not_to_have_attribute("open", "")
            method.locator("summary").click()
            expect(
                page.get_by_text("Two identities, never one score", exact=True)
            ).to_be_visible()
            page.get_by_text(
                "Supporting figures and exact archived evidence", exact=True
            ).click()
            expect(page.get_by_text("Figures", exact=True)).to_be_visible()
            check[f"research-disclosure-{width}"] = "PASS"
            choose(page, "Cluster Explorer")
            mode(page, "3d")
            page.wait_for_function(
                "document.querySelector('#explorer-space .js-plotly-plot')?.data?.[0]?.type==='scatter3d'"
            )
            page.screenshot(path=str(out / f"{width}-explorer-3d.png"), full_page=True)
            if width == 375:
                toggle = page.locator('#explorer-space [data-action="touch"]')
                expect(toggle).to_have_text("Enable rotation")
                expect(page.locator("#explorer-space .obs-explorer")).to_have_class(
                    __import__("re").compile("is-touch-locked")
                )
                toggle.tap()
                expect(toggle).to_have_text("Resume page scrolling")
                toggle.tap()
                check["mobile-rotation-opt-in"] = "PASS"
            mode(page, "2d")
            page.wait_for_function(
                "document.querySelector('#explorer-space .js-plotly-plot')?.data?.[0]?.type!=='scatter3d'"
            )
            click_sample(page, touch=width == 375)
            picker = page.get_by_role("spinbutton", name="Sample number (zero-based)")
            picker.fill("0")
            picker.press("Enter")
            expect(page.locator('#explorer-detail [data-sample="0"]')).to_be_visible(
                timeout=20000
            )
            choose(page, "Overview")
            choose(page, "Cluster Explorer")
            expect(page.locator('#explorer-detail [data-sample="0"]')).to_be_visible()
            check[f"keyboard-sample-and-tab-continuity-{width}"] = "PASS"
            page.get_by_role("button", name="Refresh live data", exact=True).click()
            expect(page.locator("#explorer-detail .obs-guide")).to_be_visible(
                timeout=20000
            )
            expect(page.locator("#explorer-detail")).to_have_attribute(
                "aria-busy", "false"
            )
            picker.fill("0")
            picker.press("Enter")
            expect(page.locator('#explorer-detail [data-sample="0"]')).to_be_visible(
                timeout=20000
            )
            page.locator("#explorer-detail .obs-selected-track").evaluate("""e => {
              e.outerHTML='<div class="obs-card obs-selection-error" data-sample="1">Simulated neighbor failure</div>';
            }""")
            expect(page.locator("#explorer-detail .obs-selection-error")).to_be_hidden()
            expect(page.locator("#explorer-detail")).to_have_attribute(
                "aria-busy", "true"
            )
            page.locator("#explorer-detail .obs-selection-error").evaluate("""e => {
              e.outerHTML='<div class="obs-card obs-selection-error" data-sample="0">Simulated neighbor failure</div>';
            }""")
            expect(
                page.locator("#explorer-detail .obs-selection-error")
            ).to_be_visible()
            expect(page.locator("#explorer-detail")).to_have_attribute(
                "aria-busy", "false"
            )
            picker.fill("1")
            picker.press("Enter")
            expect(
                page.locator('#explorer-detail .obs-selected-track[data-sample="1"]')
            ).to_be_visible(timeout=20000)
            picker.fill("0")
            picker.press("Enter")
            expect(
                page.locator('#explorer-detail .obs-selected-track[data-sample="0"]')
            ).to_be_visible(timeout=20000)
            check[f"refresh-and-selection-error-identity-{width}"] = "PASS"
            page.screenshot(
                path=str(out / f"{width}-selected-inspector.png"), full_page=True
            )
            selected_cluster = (
                page.locator("#explorer-detail h3").inner_text().split("Cluster ")[-1]
            )
            page.locator(
                f'#explorer-space [data-cluster="{1 - int(selected_cluster)}"]'
            ).click()
            expect(
                page.locator("#explorer-detail .obs-selected-track:visible")
            ).to_have_count(0)
            expect(page.locator("#explorer-detail .obs-guide")).to_be_visible(
                timeout=20000
            )
            page.locator('#explorer-space [data-cluster="all"]').click()
            mode(page, "density")
            expect(page.locator("#explorer-detail")).to_contain_text(
                "Read population density", timeout=20000
            )
            page.wait_for_function(
                "document.querySelector('#explorer-space .js-plotly-plot').data[0].type==='heatmap'"
            )
            page.locator("#explorer-space .js-plotly-plot").evaluate("""g => {
              g.emit('plotly_click', {points:[{customdata:[10,0.5,0.2]}]});
            }""")
            expect(page.locator("#explorer-detail .obs-guide")).to_be_visible()
            expect(page.locator("#explorer-detail")).to_have_attribute(
                "aria-busy", "false"
            )
            expect(page.locator("#explorer-space .obs-status")).not_to_contain_text(
                "Selected sample"
            )
            check[f"hover-click-neighbors-filter-density-{width}"] = "PASS"
            if width == 1440:
                mode(page, "3d")
                plot = page.locator("#explorer-space .js-plotly-plot")
                plot.scroll_into_view_if_needed()
                page.wait_for_function(
                    "document.querySelector('#explorer-space .js-plotly-plot')._fullLayout.scene"
                )

                def camera(plot=plot):
                    return plot.evaluate(
                        "g=>JSON.stringify(g._fullLayout.scene._scene.getCamera())"
                    )

                before = camera()
                b = plot.bounding_box()
                page.mouse.move(b["x"] + b["width"] * 0.5, b["y"] + b["height"] * 0.5)
                page.mouse.down()
                page.mouse.move(
                    b["x"] + b["width"] * 0.65, b["y"] + b["height"] * 0.65, steps=12
                )
                page.mouse.up()
                page.wait_for_timeout(300)
                rotated = camera()
                assert before != rotated, "camera did not rotate"
                page.mouse.wheel(0, -180)
                page.wait_for_timeout(300)
                zoomed = camera()
                assert zoomed != rotated, "camera did not zoom"
                rotated = zoomed
                page.locator('#explorer-space [data-cluster="0"]').click()
                page.wait_for_timeout(300)
                before_filter, after_filter = json.loads(rotated), json.loads(camera())
                assert all(
                    abs(before_filter[key][axis] - after_filter[key][axis]) < 1e-8
                    for key in ("eye", "up", "center")
                    for axis in ("x", "y", "z")
                ), ("filter reset camera", rotated, camera())
                page.get_by_role("button", name="Refresh live data", exact=True).click()
                expect(page.locator("#explorer-detail .obs-guide")).to_be_visible(
                    timeout=20000
                )
                after_refresh = json.loads(camera())
                assert all(
                    abs(before_filter[key][axis] - after_refresh[key][axis]) < 1e-8
                    for key in ("eye", "up", "center")
                    for axis in ("x", "y", "z")
                ), "refresh reset camera"
                check["refresh-camera-continuity"] = "PASS"
                page.locator('#explorer-space [data-action="reset"]').click()
                page.wait_for_timeout(300)
                assert camera() != rotated
                check["camera-rotation-filter-continuity-reset"] = "PASS"
                page.locator('#explorer-space [data-cluster="all"]').click()
                mode(page, "constellation")
                scene = "document.querySelector('#explorer-space .obs-explorer').__acousticConstellation"
                page.wait_for_function(scene, timeout=20000)
                canvas = page.locator("#explorer-space canvas.obs-constellation-canvas")
                canvas.scroll_into_view_if_needed()
                b = canvas.bounding_box()
                pos = page.evaluate(f"{scene}.projectPoint(0)")
                page.mouse.move(b["x"] + pos["x"], b["y"] + pos["y"])
                page.mouse.click(b["x"] + pos["x"], b["y"] + pos["y"])
                expect(
                    page.locator("#explorer-detail .obs-selected-track")
                ).to_be_visible(timeout=20000)
                page.mouse.move(b["x"] + b["width"] * 0.5, b["y"] + b["height"] * 0.5)
                page.mouse.down()
                page.mouse.move(
                    b["x"] + b["width"] * 0.6, b["y"] + b["height"] * 0.6, steps=8
                )
                page.mouse.up()
                assert pos != page.evaluate(f"{scene}.projectPoint(0)")
                page.screenshot(
                    path=str(out / "1440-constellation.png"), full_page=True
                )
                page.evaluate(f"window.__oldScene={scene}")
                projected_before = page.evaluate(f"{scene}.projectPoint(0)")
                page.get_by_role("button", name="Refresh live data", exact=True).click()
                expect(page.locator("#explorer-detail .obs-guide")).to_be_visible(
                    timeout=20000
                )
                assert page.evaluate(f"window.__oldScene === {scene}")
                projected_after = page.evaluate(f"{scene}.projectPoint(0)")
                assert all(
                    abs(projected_before[axis] - projected_after[axis]) < 1e-8
                    for axis in ("x", "y")
                ), "refresh reset constellation camera"
                expect(page.locator("#explorer-detail")).to_have_attribute(
                    "aria-busy", "false"
                )
                check["refresh-constellation-reuse-camera-continuity"] = "PASS"
                page.locator('#explorer-space [data-cluster="0"]').click()
                assert page.evaluate(f"window.__oldScene === {scene}")
                mode(page, "density")
                assert (
                    page.locator(
                        "#explorer-space canvas.obs-constellation-canvas"
                    ).count()
                    == 0
                )
                check["constellation-render-pick-filter-reuse-dispose"] = "PASS"
            page.close()
        if interactions:
            page = browser.new_page(reduced_motion="reduce")
            ready(page, base)
            duration = page.locator(".obs-card").first.evaluate(
                "e=>parseFloat(getComputedStyle(e).transitionDuration)"
            )
            assert duration < 0.01
            page.locator('#overview-space [data-view="density"]').focus()
            assert (
                page.locator('#overview-space [data-view="density"]').evaluate(
                    "e=>getComputedStyle(e).outlineStyle"
                )
                == "solid"
            )
            page.keyboard.press("Enter")
            expect(
                page.locator('#overview-space [data-view="density"]')
            ).to_have_attribute("aria-pressed", "true")
            check["keyboard-focus-reduced-motion"] = "PASS"
            page.close()
            page = browser.new_page()
            page.route("**/constellation-*.js", lambda route: route.abort())
            ready(page, base)
            choose(page, "Cluster Explorer")
            page.locator('#explorer-space [data-view="constellation"]').click()
            expect(
                page.locator('#explorer-space [data-view="density"]')
            ).to_have_attribute("aria-pressed", "true", timeout=20000)
            check["constellation-load-fallback"] = "PASS"
            page.close()
            page = browser.new_page()
            page.add_init_script("""const get=HTMLCanvasElement.prototype.getContext;
              HTMLCanvasElement.prototype.getContext=function(kind,...args){
                return /webgl/.test(kind) ? null : get.call(this,kind,...args);
              };""")
            ready(page, base)
            choose(page, "Cluster Explorer")
            expect(page.locator('#explorer-space [data-view="3d"]')).to_be_disabled()
            expect(
                page.locator('#explorer-space [data-view="constellation"]')
            ).to_be_disabled()
            page.wait_for_function(
                "document.querySelector('#explorer-space .js-plotly-plot').data[0].type==='scatter'"
            )
            check["webgl-unavailable-svg-fallback"] = "PASS"
            page.close()
        browser.close()
    return evidence


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:7872/")
    parser.add_argument("--capture-only", action="store_true")
    parser.add_argument("--width", type=int)
    parser.add_argument("--output", default="points")
    args = parser.parse_args()
    evidence = run(args.base, REPORTS / args.output, not args.capture_only, args.width)
    (REPORTS / f"{args.output}-browser.json").write_text(
        json.dumps(evidence, indent=2), encoding="utf-8"
    )
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
