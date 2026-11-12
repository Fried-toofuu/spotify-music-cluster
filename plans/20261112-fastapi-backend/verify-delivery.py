"""Collect backend verification evidence without refitting or retaining input rows."""

import importlib.metadata
import json
import re
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path

from spotify_cluster.data import sha256_file
from spotify_cluster.model_store import load_bundle

PLAN = Path(__file__).resolve().parent
ROOT = PLAN.parents[1]
REPORTS = PLAN / "reports"


def run(name, command, cwd=ROOT):
    result = subprocess.run(
        command, cwd=cwd, capture_output=True, text=True, check=False
    )
    (REPORTS / f"{name}.txt").write_text(
        result.stdout + result.stderr, encoding="utf-8"
    )
    if result.returncode:
        raise RuntimeError(f"{name} failed ({result.returncode}); see saved log")
    print(f"{name}: PASS", flush=True)
    return result.stdout.strip()


def main():
    commands = {
        "pytest": [sys.executable, "-m", "pytest", "-q"],
        "pytest-real-api": [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "tests/test_api_real_model.py",
            "--run-real-api",
        ],
        "ruff-check": [sys.executable, "-m", "ruff", "check", "."],
        "ruff-format": [sys.executable, "-m", "ruff", "format", "--check", "."],
        "build": [sys.executable, "-m", "build"],
        "http-smoke": [sys.executable, str(PLAN / "verify-http.py")],
        "pip-check": [sys.executable, "-m", "pip", "check"],
    }
    evidence = {
        "tools": {
            name: importlib.metadata.version(name)
            for name in (
                "fastapi",
                "pydantic",
                "uvicorn",
                "starlette",
                "httpx",
                "pytest",
                "ruff",
                "build",
            )
        },
        "checks": {},
    }
    for name, command in commands.items():
        evidence["checks"][name] = run(name, command)
    wheel = ROOT / "dist" / "spotify_music_clustering_web-0.1.0-py3-none-any.whl"
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        api_modules = [
            name for name in names if name.startswith("spotify_cluster/api/")
        ]
        assert len(api_modules) == 5
        assert not any(
            name.endswith((".csv", ".joblib", ".ipynb"))
            or "verification_sample" in name
            for name in names
        )
        evidence["wheel_api_modules"] = api_modules
    with tarfile.open(
        ROOT / "dist" / "spotify_music_clustering_web-0.1.0.tar.gz"
    ) as archive:
        names = archive.getnames()
        assert not any(
            name.endswith((".csv", ".joblib", ".ipynb"))
            or "verification_sample" in name
            for name in names
        )
    evidence["private_distribution_exclusion"] = "PASS"
    wheel_python = ROOT / ".venv-api-wheel" / "Scripts" / "python.exe"
    run(
        "wheel-refresh",
        [
            str(wheel_python),
            "-m",
            "pip",
            "install",
            "--force-reinstall",
            "--no-deps",
            str(wheel),
        ],
    )
    run("wheel-pip-check", [str(wheel_python), "-m", "pip", "check"])
    with tempfile.TemporaryDirectory(prefix="spotify-api-wheel-") as outside:
        evidence["installed_wheel"] = json.loads(
            run(
                "wheel-api",
                [
                    str(wheel_python),
                    "-I",
                    str(PLAN / "verify-installed-api.py"),
                    str(ROOT / "artifacts" / "deployment-v1"),
                ],
                cwd=outside,
            )
        )
        run(
            "wheel-cli",
            [
                str(wheel_python),
                "-I",
                str(ROOT / "scripts" / "export_model.py"),
                "--help",
            ],
            cwd=outside,
        )
    before = json.loads((REPORTS / "protected-before.json").read_text())
    after = {name: sha256_file(ROOT / name) for name in before}
    (REPORTS / "protected-after.json").write_text(json.dumps(after, indent=2) + "\n")
    assert after == before
    evidence["protected_files_unchanged"] = True
    _, metadata, profiles = load_bundle(ROOT / "artifacts" / "deployment-v1")
    evidence["model"] = {
        "model_id": metadata["model_id"],
        "artifact_sha256": metadata["artifact_sha256"],
        "cluster_counts": metadata["cluster_counts"],
        "instrumentalness_between_ss_share": profiles["feature_contributions"][
            "shares"
        ]["instrumentalness"],
        "historical_equivalence": metadata["historical_equivalence"],
    }
    broken = []
    for document in (
        ROOT / "README.md",
        ROOT / "AGENTS.md",
        ROOT / "docs" / "API.md",
        ROOT / "docs" / "ARCHITECTURE.md",
    ):
        for target in re.findall(
            r"\]\(([^)]+)\)", document.read_text(encoding="utf-8")
        ):
            if (
                "://" not in target
                and not (document.parent / target.split("#")[0]).exists()
            ):
                broken.append(f"{document.name}: {target}")
    assert not broken, broken
    evidence["documentation_links"] = "PASS"
    evidence["wheel_sha256"] = sha256_file(wheel)
    evidence["http_smoke"] = json.loads((REPORTS / "http-smoke.json").read_text())
    (REPORTS / "evidence.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print("Artifact preservation, distribution privacy and documentation links: PASS")


if __name__ == "__main__":
    main()
