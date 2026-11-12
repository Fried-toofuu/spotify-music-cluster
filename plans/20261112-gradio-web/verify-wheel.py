"""Install the built web wheel in its own venv and inspect it outside the checkout."""

import json
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORTS = Path(__file__).resolve().parent / "reports"


def main():
    environment = ROOT / ".venv-web-wheel"
    if not environment.exists():
        subprocess.run([sys.executable, "-m", "venv", str(environment)], check=True)
    python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    wheel = next((ROOT / "dist").glob("*.whl"))
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        assert "spotify_cluster/web/app.py" in names
        assert not any(n.endswith((".csv", ".ipynb", ".joblib")) for n in names)
        assert not any("verification_sample" in n for n in names)
    commands = {
        "wheel-pip-upgrade": ["-m", "pip", "install", "--upgrade", "pip>=26.2.2"],
        "wheel-install": [
            "-m",
            "pip",
            "install",
            "--force-reinstall",
            str(wheel) + "[api,web]",
        ],
        "wheel-pip-check": ["-m", "pip", "check"],
        "wheel-import": [
            "-I",
            str(Path(__file__).with_name("verify-installed-web.py")),
        ],
    }
    evidence = {}
    with tempfile.TemporaryDirectory(prefix="spotify-wheel-web-") as outside:
        for name, args in commands.items():
            with (REPORTS / f"{name}.txt").open("w", encoding="utf-8") as log:
                result = subprocess.run(
                    [str(python), *args],
                    cwd=outside,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                )
            evidence[name] = result.returncode
            print(name, result.returncode, flush=True)
            if result.returncode:
                break
    evidence["wheel_has_no_private_data"] = True
    (REPORTS / "wheel.json").write_text(json.dumps(evidence, indent=2) + "\n")
    assert all(
        value == 0
        for key, value in evidence.items()
        if key != "wheel_has_no_private_data"
    )


if __name__ == "__main__":
    main()
