"""Owned aggregate-mode verification and distributable screenshot capture."""

import importlib.util
import json
import shutil
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parents[1]


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    servers = load(
        ROOT / "plans/20261112-acoustic-observatory/verify-live.py", "servers"
    )
    checks = load(HERE / "verify-browser.py", "checks")
    if not (servers.port_free(8010) and servers.port_free(7871)):
        raise RuntimeError("Aggregate verification ports already have owners")
    api = servers.start_api()
    web = servers.start_web()
    try:
        servers.wait_ready(api, "http://127.0.0.1:8010/api/v1/health")
        servers.wait_ready(web, "http://127.0.0.1:7871/")
        out = HERE / "reports/aggregate"
        evidence = checks.run("http://127.0.0.1:7871/", out, interactions=False)
        integration = servers.browser_checks("http://127.0.0.1:7871/", out / "workflow")
        evidence["integration"] = integration
        shots = ROOT / "docs/screenshots"
        for name, source in {
            "overview-1440.png": out / "1440-overview-viewport.png",
            "overview-375.png": out / "375-overview-viewport.png",
            "explorer-density-1440.png": out / "1440-explorer.png",
            "predict-result-1440.png": out / "workflow/1440-predict.png",
            "research-1440.png": out / "1440-research.png",
        }.items():
            shutil.copyfile(source, shots / name)
    finally:
        servers.stop(web)
        servers.stop(api)
        servers.wait_port_free(7871)
        servers.wait_port_free(8010)
    evidence["ports_released"] = {
        str(port): servers.port_free(port) for port in (7871, 8010)
    }
    (HERE / "reports/aggregate-browser.json").write_text(
        json.dumps(evidence, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "checks": evidence["checks"],
                "errors": evidence["errors"],
                "integration": integration["status"],
                "ports_released": evidence["ports_released"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
