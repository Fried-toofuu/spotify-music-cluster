"""Verify delivery without fitting research data or evaluating Holdout."""

import importlib.metadata
import json
import re
import subprocess
import sys
import tarfile
import venv
import zipfile
from pathlib import Path

from spotify_cluster.config import F9
from spotify_cluster.data import load_dataset, sha256_file
from spotify_cluster.model_store import environment

ROOT = Path(__file__).resolve().parents[2]
REPORTS = Path(__file__).resolve().parent / "reports"


def run(name, args, *, expected=0, cwd=ROOT):
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=False)
    output = result.stdout + result.stderr
    (REPORTS / f"{name}.txt").write_text(output, encoding="utf-8")
    if result.returncode != expected:
        raise RuntimeError(f"{name}: exit {result.returncode}; see saved log")
    print(f"{name}: expected exit {expected}", flush=True)
    return output


def main():
    REPORTS.mkdir(parents=True, exist_ok=True)
    evidence = {"environment": environment()}
    evidence["development_tools"] = {
        name: importlib.metadata.version(name)
        for name in ("pip", "pytest", "ruff", "build", "pip-audit")
    }
    notebook = ROOT / "Spotify_Music_Clustering_Final.ipynb"
    evidence["notebook_sha256"] = sha256_file(notebook)
    evidence["notebook_cells"] = len(
        json.loads(notebook.read_text(encoding="utf-8"))["cells"]
    )
    prepared, identity = load_dataset(ROOT / "dataset.csv")
    evidence["dataset"] = identity
    evidence["matrix_shape"] = list(prepared.matrix.shape)
    evidence["features"] = list(F9)
    output = ROOT / "artifacts" / "final_model"
    assert not output.exists(), "Do not overwrite an existing model"
    run(
        "export-cli",
        [
            sys.executable,
            "scripts/export_model.py",
            "--dataset",
            "dataset.csv",
            "--output",
            str(output),
        ],
        expected=2,
    )
    assert not output.exists()
    evidence["production_export"] = "BLOCKED"
    evidence["pytest_output"] = run("pytest", [sys.executable, "-m", "pytest", "-q"])
    run("ruff-check", [sys.executable, "-m", "ruff", "check", "."])
    run("ruff-format", [sys.executable, "-m", "ruff", "format", "--check", "."])
    run("build", [sys.executable, "-m", "build"])
    wheel = ROOT / "dist" / "spotify_music_clustering_web-0.1.0-py3-none-any.whl"
    source = ROOT / "dist" / "spotify_music_clustering_web-0.1.0.tar.gz"
    with zipfile.ZipFile(wheel) as archive:
        wheel_names = archive.namelist()
    with tarfile.open(source) as archive:
        source_names = archive.getnames()
    for name in wheel_names + source_names:
        assert not name.endswith((".csv", ".ipynb", ".joblib"))
        assert ".venv" not in name and "/.env" not in name
    assert all(
        name.startswith(("spotify_cluster/", "spotify_music_clustering_web-"))
        for name in wheel_names
    )
    assert any(name.endswith("scripts/export_model.py") for name in source_names)
    assert any(name.endswith("tests/conftest.py") for name in source_names)
    evidence["wheel_contents"] = wheel_names
    evidence["sdist_contents"] = source_names
    evidence["packages"] = {
        p.name: {"bytes": p.stat().st_size, "sha256": sha256_file(p)}
        for p in (wheel, source)
    }
    clean_dir = ROOT / ".venv-wheel"
    if not clean_dir.exists():
        venv.EnvBuilder(with_pip=True).create(clean_dir)
    clean_python = clean_dir / "Scripts" / "python.exe"
    run(
        "wheel-pip-upgrade",
        [str(clean_python), "-m", "pip", "install", "--upgrade", "pip>=26.2.2"],
    )
    run(
        "wheel-install",
        [str(clean_python), "-m", "pip", "install", "--force-reinstall", str(wheel)],
    )
    run("wheel-pip-check", [str(clean_python), "-m", "pip", "check"])
    code = """
import json, tempfile
from pathlib import Path
import numpy as np
import spotify_cluster
from spotify_cluster.config import F9, PREPARATION_VERSION
from spotify_cluster.inference import InferenceService
from spotify_cluster.model_store import make_metadata, new_model_id, save_bundle
from spotify_cluster.training import train_model, verify_numerics, cluster_profiles
rng = np.random.default_rng(71)
x = rng.uniform(.1, .9, (40, 9))
x[:, 4] *= 200
x[:, 5] *= -30
x[:20, 7], x[20:, 7] = 0, 1
params = dict(n_clusters=2, init="k-means++", n_init=5, max_iter=300,
              tol=1e-4, algorithm="lloyd", random_state=42, copy_x=True, verbose=0)
p = train_model(x, params)
model_id = new_model_id()
identity = dict(dataset_sha256="software-fixture",
                prepared_fingerprint="software-fixture",
                preparation_version=PREPARATION_VERSION,
                training_sample_count=len(x))
m = make_metadata(p, model_id, identity, reconstruction_status="software-test-only")
with tempfile.TemporaryDirectory() as temporary:
    out = Path(temporary) / "software-fixture"
    save_bundle(out, p, m, cluster_profiles(p, x, model_id), verify_numerics(p, x))
    service = InferenceService(out)
    track = dict(zip(F9, x[0].tolist()))
    one = service.predict_one(track)
    assert service.predict_batch([track, track]) == [one, one]
    assert one["cluster_id"] == int(p.predict(x[:1])[0])
    print(json.dumps({"import_path": spotify_cluster.__file__,
                      "fixture_only": True, "single_batch_roundtrip": "PASS"}))
"""
    smoke = run(
        "wheel-clean-process", [str(clean_python), "-I", "-c", code], cwd=REPORTS
    )
    assert ".venv-wheel" in json.loads(smoke)["import_path"]
    evidence["fresh_wheel_smoke"] = json.loads(smoke)
    links = []
    for doc in [ROOT / "README.md", ROOT / "AGENTS.md", *(ROOT / "docs").glob("*.md")]:
        for target in re.findall(r"\]\(([^)]+)\)", doc.read_text(encoding="utf-8")):
            if "://" not in target and not target.startswith("#"):
                assert (doc.parent / target.split("#")[0]).exists(), (doc.name, target)
                links.append(f"{doc.relative_to(ROOT)}: {target}")
    evidence["verified_local_links"] = links
    (REPORTS / "evidence.json").write_text(
        json.dumps(evidence, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "matrix_shape": evidence["matrix_shape"],
                "production_export": "BLOCKED",
                "software_checks": "PASS",
            }
        )
    )


if __name__ == "__main__":
    main()
