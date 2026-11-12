"""Copy vetted browser assets to a Gradio-served directory outside the checkout."""

from __future__ import annotations

import hashlib
import shutil
import tempfile
from pathlib import Path
from urllib.parse import quote

import gradio as gr

ASSET_DIR = Path(tempfile.gettempdir()) / "acoustic-observatory-assets"
PACKAGE_STATIC = Path(__file__).parent / "static"


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def asset_url(source: Path) -> str:
    source = Path(source)
    if not source.is_file():
        raise RuntimeError("A required browser asset is missing from its package")
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    digest = _digest(source)
    target = ASSET_DIR / f"{source.stem}-{digest}{source.suffix}"
    if not target.is_file() or _digest(target) != digest:
        shutil.copyfile(source, target)
    return "/gradio_api/file=" + quote(target.as_posix(), safe="/:")


def plotly_head() -> str:
    import plotly

    source = Path(plotly.__file__).parent / "package_data" / "plotly.min.js"
    return f'<script src="{asset_url(source)}"></script>'


def constellation_url() -> str:
    return asset_url(PACKAGE_STATIC / "constellation.js")


def register_assets() -> None:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    gr.set_static_paths([ASSET_DIR])
