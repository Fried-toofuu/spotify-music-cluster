"""Record local regression, package, dependency and preservation evidence."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORTS = Path(__file__).resolve().parent / "reports"


def main():
    evidence = {}
    commands = {
        "pytest": ["pytest", "-q"],
        "pytest-real-api": [
            "pytest",
            "-q",
            "tests/test_api_real_model.py",
            "--run-real-api",
        ],
        "ruff-check": ["ruff", "check", "."],
        "ruff-format": ["ruff", "format", "--check", "."],
        "build": ["build"],
        "pip-check": ["pip", "check"],
    }
    for name, args in commands.items():
        with (REPORTS / f"{name}.txt").open("w", encoding="utf-8") as log:
            result = subprocess.run(
                [sys.executable, "-m", *args],
                cwd=ROOT,
                stdout=log,
                stderr=subprocess.STDOUT,
            )
        evidence[name] = {
            "exit_code": result.returncode,
            "command": "python -m " + " ".join(args),
        }
        print(name, result.returncode, flush=True)
    before = json.loads((ROOT / ".venv/web-protected-before.json").read_text())
    after = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in before}
    evidence["protected_files_unchanged"] = before == after
    (REPORTS / "protected-files.json").write_text(json.dumps(after, indent=2) + "\n")
    (REPORTS / "gates.json").write_text(json.dumps(evidence, indent=2) + "\n")
    assert before == after
    assert all(v["exit_code"] == 0 for v in evidence.values() if isinstance(v, dict))


if __name__ == "__main__":
    main()
