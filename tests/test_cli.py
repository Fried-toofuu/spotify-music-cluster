import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "export_model.py"


def test_cli_rejects_wrong_snapshot_without_output(tmp_path):
    dataset = tmp_path / "dataset.csv"
    dataset.write_text("not the authorized snapshot")
    output = tmp_path / "model"
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--dataset",
            str(dataset),
            "--output",
            str(output),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert "SHA-256" in result.stderr
    assert not output.exists()


def test_cli_refuses_existing_directory(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--dataset",
            "missing.csv",
            "--output",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert "already exists" in result.stderr
