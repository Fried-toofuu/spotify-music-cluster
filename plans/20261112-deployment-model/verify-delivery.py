"""Record actual deployment acceptance evidence without publishing private samples."""

import importlib.metadata
import json
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import venv
import zipfile
from pathlib import Path

from spotify_cluster.config import DEPLOYMENT_V1
from spotify_cluster.data import sha256_file
from spotify_cluster.model_store import environment, load_bundle

PLAN = Path(__file__).resolve().parent
ROOT = PLAN.parents[1]
REPORTS = PLAN / "reports"
ARTIFACT = ROOT / "artifacts" / "deployment-v1"
NOTEBOOK_SHA256 = "76a31ac55e385238761d7decbc5117cede6f1ad8a2c9285504e80c4a2526b178"


def run(name, command, *, cwd=ROOT):
    result = subprocess.run(
        command, cwd=cwd, capture_output=True, text=True, check=False
    )
    (REPORTS / f"{name}.txt").write_text(
        result.stdout + result.stderr, encoding="utf-8"
    )
    if result.returncode:
        raise RuntimeError(f"{name} failed: exit {result.returncode}; see saved log")
    print(f"{name}: PASS", flush=True)
    return result.stdout


def main():
    REPORTS.mkdir(parents=True, exist_ok=True)
    pipeline, metadata, profiles = load_bundle(ARTIFACT)
    assert metadata["deployment_profile"] == DEPLOYMENT_V1.identifier
    evidence = {
        "environment": environment(),
        "metadata": metadata,
        "profiles": profiles,
        "tools": {
            name: importlib.metadata.version(name)
            for name in ("pip", "pytest", "ruff", "build", "pip-audit")
        },
    }
    evidence["unit_tests"] = run("pytest", [sys.executable, "-m", "pytest", "-q"])
    evidence["real_model_tests"] = run(
        "pytest-real-model",
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/test_real_model.py",
            "-q",
            "--run-real-model",
        ],
    )
    run("ruff-check", [sys.executable, "-m", "ruff", "check", "."])
    run("ruff-format", [sys.executable, "-m", "ruff", "format", "--check", "."])
    run("build", [sys.executable, "-m", "build"])
    wheel = ROOT / "dist" / "spotify_music_clustering_web-0.1.0-py3-none-any.whl"
    source = ROOT / "dist" / "spotify_music_clustering_web-0.1.0.tar.gz"
    with zipfile.ZipFile(wheel) as archive:
        evidence["wheel_contents"] = archive.namelist()
    with tarfile.open(source) as archive:
        evidence["sdist_contents"] = archive.getnames()
    for name in evidence["wheel_contents"] + evidence["sdist_contents"]:
        assert not name.endswith((".csv", ".ipynb", ".joblib"))
        assert "verification_sample" not in name and ".venv" not in name
        assert "/artifacts/" not in name and "/.env" not in name
    evidence["packages"] = {
        file.name: {"bytes": file.stat().st_size, "sha256": sha256_file(file)}
        for file in (wheel, source)
    }
    clean = ROOT / ".venv-deployment-check"
    if not clean.exists():
        venv.EnvBuilder(with_pip=True).create(clean)
    python = clean / "Scripts" / "python.exe"
    run(
        "wheel-pip-upgrade",
        [str(python), "-m", "pip", "install", "--upgrade", "pip>=26.2.2"],
    )
    run(
        "wheel-install",
        [str(python), "-m", "pip", "install", "--force-reinstall", str(wheel)],
    )
    run("wheel-pip-check", [str(python), "-m", "pip", "check"])
    # Copy only the bundle into an isolated working directory; no CSV or notebook.
    with tempfile.TemporaryDirectory(prefix="spotify-inference-") as temporary:
        isolation = Path(temporary)
        local_bundle = isolation / "deployment-v1"
        shutil.copytree(ARTIFACT, local_bundle)
        smoke = run(
            "wheel-real-inference",
            [
                str(python),
                "-I",
                str(PLAN / "verify-installed-model.py"),
                "--artifacts",
                str(local_bundle),
            ],
            cwd=isolation,
        )
        evidence["wheel_inference"] = json.loads(smoke)
        assert (
            ".venv-deployment-check"
            in evidence["wheel_inference"]["package_import_path"]
        )
    run(
        "dependency-audit",
        [
            sys.executable,
            "-m",
            "pip_audit",
            "--format",
            "json",
            "--output",
            str(REPORTS / "dependency-audit.json"),
        ],
    )
    run(
        "wheel-dependency-audit",
        [
            sys.executable,
            "-m",
            "pip_audit",
            "--path",
            str(clean / "Lib" / "site-packages"),
            "--format",
            "json",
            "--output",
            str(REPORTS / "wheel-dependency-audit.json"),
        ],
    )
    notebook = ROOT / "Spotify_Music_Clustering_Final.ipynb"
    evidence["notebook_sha256"] = sha256_file(notebook)
    assert evidence["notebook_sha256"] == NOTEBOOK_SHA256
    evidence["artifacts"] = {
        file.name: {"bytes": file.stat().st_size, "sha256": sha256_file(file)}
        for file in sorted(ARTIFACT.iterdir())
        if file.is_file()
    }
    for file in ARTIFACT.iterdir():
        subprocess.run(
            [
                "git",
                "-c",
                f"safe.directory={ROOT.as_posix()}",
                "check-ignore",
                "--quiet",
                str(file),
            ],
            check=True,
            cwd=ROOT,
        )
    links = []
    for doc in (ROOT / "README.md", ROOT / "AGENTS.md", *(ROOT / "docs").glob("*.md")):
        for target in re.findall(r"\]\(([^)]+)\)", doc.read_text(encoding="utf-8")):
            if "://" not in target and not target.startswith("#"):
                assert (doc.parent / target.split("#")[0]).exists(), (doc.name, target)
                links.append(f"{doc.relative_to(ROOT)}: {target}")
    evidence["local_links"] = links
    (REPORTS / "evidence.json").write_text(
        json.dumps(evidence, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "model_id": metadata["model_id"],
                "cluster_counts": metadata["cluster_counts"],
                "deployment_verification": "PASS",
                "historical_equivalence": "NOT VERIFIED",
            }
        )
    )


if __name__ == "__main__":
    main()
