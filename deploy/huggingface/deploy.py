"""Deploy the public aggregate Space; private artifacts stay in a private dataset."""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
import time
from pathlib import Path

import httpx
from huggingface_hub import HfApi, get_token

ROOT = Path(__file__).resolve().parents[2]
DEPLOY = Path(__file__).resolve().parent
IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", "*.egg-info")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--space",
        help="Space repo id (default: <user>/acoustic-observatory)",
    )
    parser.add_argument(
        "--dataset",
        help=(
            "Private artifact dataset id "
            "(default: <user>/acoustic-observatory-artifacts)"
        ),
    )
    parser.add_argument(
        "--visualization-mode",
        choices=("aggregate", "points"),
        default="aggregate",
        help="aggregate is the safe public default; points requires explicit approval",
    )
    parser.add_argument(
        "--allow-public-points",
        action="store_true",
        help="Explicitly allow per-track points visualization in the public app",
    )
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--skip-wait", action="store_true")
    return parser.parse_args()


def check_artifacts(mode: str) -> tuple[Path, Path, Path]:
    model = ROOT / "artifacts" / "deployment-v1"
    visualization = (
        ROOT / "artifacts" / "visualization-public-v1"
        if mode == "aggregate"
        else ROOT / "artifacts" / "visualization-v1"
    )
    research = ROOT / "artifacts" / "research-v1"
    for path in (model, visualization, research):
        if not path.is_dir():
            raise RuntimeError(
                f"Missing artifact directory: {path}. Prepare artifacts first."
            )
    return model, visualization, research


def stage_space() -> Path:
    staging = Path(tempfile.mkdtemp(prefix="acoustic-observatory-space-"))
    shutil.copytree(ROOT / "src", staging / "src", ignore=IGNORE)
    for name in ("pyproject.toml", "constraints.txt", "MANIFEST.in"):
        shutil.copy2(ROOT / name, staging / name)
    for name in ("README.md", "Dockerfile"):
        shutil.copy2(DEPLOY / name, staging / name)
    shutil.copy2(ROOT / "deploy" / "entrypoint.sh", staging / "entrypoint.sh")
    return staging


def main() -> int:
    args = parse_args()
    if args.visualization_mode == "points" and not args.allow_public_points:
        raise SystemExit(
            "Refusing public points mode without --allow-public-points. "
            "Per-track derived coordinates require explicit redistribution approval."
        )
    token = get_token()
    if not token:
        print(
            "No Hugging Face token found. Run:\n"
            "  .\\.venv\\Scripts\\python.exe -c "
            '"from huggingface_hub import login; login()"',
            file=sys.stderr,
        )
        return 2
    api = HfApi(token=token)
    user = api.whoami()["name"]
    space_id = args.space or f"{user}/acoustic-observatory"
    dataset_id = args.dataset or f"{user}/acoustic-observatory-artifacts"
    model, visualization, research = check_artifacts(args.visualization_mode)

    print(f"[1/6] Private artifact dataset: {dataset_id}")
    api.create_repo(dataset_id, repo_type="dataset", private=True, exist_ok=True)
    if not api.repo_info(dataset_id, repo_type="dataset").private:
        raise RuntimeError(
            "Refusing to upload private model/verification data to a public dataset"
        )
    api.upload_folder(
        repo_id=dataset_id,
        repo_type="dataset",
        folder_path=str(model),
        path_in_repo="deployment-v1",
        commit_message="Add trusted deployment model (private)",
    )
    api.upload_folder(
        repo_id=dataset_id,
        repo_type="dataset",
        folder_path=str(visualization),
        path_in_repo="visualization",
        commit_message=f"Add {args.visualization_mode} visualization artifact",
    )
    api.upload_folder(
        repo_id=dataset_id,
        repo_type="dataset",
        folder_path=str(research),
        path_in_repo="research-v1",
        commit_message="Add research comparison artifact",
    )

    print(f"[2/6] Public Space: {space_id}")
    api.create_repo(
        space_id,
        repo_type="space",
        space_sdk="docker",
        private=False,
        exist_ok=True,
    )
    staging = stage_space()
    try:
        print("[3/6] Uploading Space code")
        api.upload_folder(
            repo_id=space_id,
            repo_type="space",
            folder_path=str(staging),
            commit_message="Deploy Acoustic Observatory",
        )
    finally:
        shutil.rmtree(staging, ignore_errors=True)

    print("[4/6] Configuring Space secret and variables")
    api.add_space_secret(
        space_id,
        "HF_TOKEN",
        token,
        description="Read access to the private artifact dataset",
    )
    api.add_space_variable(space_id, "ARTIFACT_DATASET", dataset_id)
    api.add_space_variable(
        space_id, "PUBLIC_MODE", "1" if args.visualization_mode == "aggregate" else "0"
    )

    url = f"https://{space_id.replace('/', '-').replace('_', '-')}.hf.space"
    print(f"[5/6] Space page: https://huggingface.co/spaces/{space_id}")
    print(f"[6/6] App URL (after build/start): {url}")
    if args.skip_wait:
        return 0

    deadline = time.monotonic() + args.timeout
    last_stage = None
    while time.monotonic() < deadline:
        runtime = api.get_space_runtime(space_id)
        stage = runtime.stage
        if stage != last_stage:
            print(f"Space stage: {stage}")
            last_stage = stage
        if stage == "RUNNING":
            break
        if stage in {"BUILD_ERROR", "CONFIG_ERROR", "PAUSED", "STOPPED"}:
            raise RuntimeError(f"Space did not start: {stage}")
        time.sleep(15)
    else:
        raise TimeoutError("Space build/start timeout")

    print("Space is running; checking the public app...")
    deadline = time.monotonic() + 240
    while time.monotonic() < deadline:
        try:
            response = httpx.get(
                url, timeout=30, follow_redirects=True, trust_env=False
            )
            if response.status_code == 200 and "Acoustic Observatory" in response.text:
                print(f"LIVE: {url}")
                print(f"Space: https://huggingface.co/spaces/{space_id}")
                print(
                    f"Private artifacts: https://huggingface.co/datasets/{dataset_id}"
                )
                return 0
        except httpx.HTTPError:
            pass
        time.sleep(5)
    raise TimeoutError("Space is running but the app did not answer in time")


if __name__ == "__main__":
    raise SystemExit(main())
