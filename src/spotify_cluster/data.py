"""Canonical preparation from notebook cells 18 and 21-25."""

import hashlib
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from .config import (
    BOUNDED,
    EXPECTED_SHA256,
    F9,
    GENRE_COUNT,
    PREPARATION_VERSION,
    RAW_COLUMNS,
    RAW_ROWS,
    TRACK_COUNT,
)


def sha256_file(path: Path) -> str:
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def validate_matrix(matrix: np.ndarray) -> np.ndarray:
    """Reject invalid geometry without clipping or imputation; tempo zero is valid."""
    matrix = np.asarray(matrix, dtype=np.float64)
    if matrix.ndim != 2 or matrix.shape[1] != len(F9) or not len(matrix):
        raise ValueError("Expected a nonempty (n, 9) F9 matrix")
    if not np.isfinite(matrix).all():
        raise ValueError("F9 features must be finite")
    for name in BOUNDED:
        values = matrix[:, F9.index(name)]
        if ((values < 0) | (values > 1)).any():
            raise ValueError(f"{name} must be between 0 and 1")
    if (matrix[:, F9.index("tempo")] < 0).any():
        raise ValueError("tempo must be nonnegative")
    return matrix


@dataclass
class PreparedData:
    tracks: pd.DataFrame
    genre_bridge: pd.DataFrame
    matrix: np.ndarray
    fingerprint: str


def prepare_tracks(raw: pd.DataFrame) -> PreparedData:
    """Keep the first genre-sorted source row after tolerance-based vector checks."""
    required = {"track_id", "track_genre", *F9}
    if raw.columns.duplicated().any() or not required.issubset(raw.columns):
        raise ValueError("Missing or duplicate required columns")
    working = raw.copy(deep=True)
    for column in ("track_id", "track_genre"):
        working[column] = (
            working[column].astype("string").str.strip().replace("", pd.NA)
        )
    if working["track_id"].isna().any():
        raise ValueError("Missing track_id; manual audit required")
    for name in F9:
        if working[name].map(lambda v: isinstance(v, (bool, np.bool_))).any():
            raise ValueError(f"Boolean {name} is not a numeric descriptor")
        working[name] = pd.to_numeric(working[name], errors="raise").astype("float64")
    validate_matrix(working.loc[:, F9].to_numpy())
    groups = working.groupby("track_id", sort=True)[list(F9)]
    consistent = np.isclose(
        groups.min().to_numpy(), groups.max().to_numpy(), rtol=1e-6, atol=1e-8
    ).all(axis=1)
    if not consistent.all():
        raise ValueError("Same-ID F9 feature conflict; refusing deduplication")
    bridge = (
        working.loc[working["track_genre"].notna(), ["track_id", "track_genre"]]
        .drop_duplicates()
        .rename(columns={"track_genre": "genre"})
        .sort_values(["track_id", "genre"])
        .reset_index(drop=True)
    )
    ordered = working.assign(_source_row=np.arange(len(working))).sort_values(
        ["track_id", "track_genre", "_source_row"], kind="stable", na_position="last"
    )
    tracks = (
        ordered.drop_duplicates("track_id", keep="first")
        .drop(columns=["track_genre", "_source_row", "Unnamed: 0"], errors="ignore")
        .sort_values("track_id")
        .reset_index(drop=True)
    )
    matrix = tracks.loc[:, F9].to_numpy(dtype=np.float64)
    digest = hashlib.sha256(PREPARATION_VERSION.encode())
    for track_id in tracks["track_id"]:
        encoded = track_id.encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "little"))
        digest.update(encoded)
    digest.update(matrix.astype("<f8").tobytes(order="C"))
    return PreparedData(tracks, bridge, matrix, digest.hexdigest())


def load_dataset(path: Path) -> tuple[PreparedData, dict]:
    """Only the exact authorized snapshot may enter the offline export route."""
    path = Path(path)
    checksum = sha256_file(path)
    if checksum != EXPECTED_SHA256:
        raise ValueError("Dataset SHA-256 differs from the authorized snapshot")
    raw = pd.read_csv(
        path, dtype={"track_id": "string", "track_genre": "string"}, low_memory=False
    )
    if set(raw.columns) != set(RAW_COLUMNS) or raw.shape != (RAW_ROWS, 21):
        raise ValueError("Unexpected raw dataset schema or record count")
    prepared = prepare_tracks(raw)
    if len(prepared.tracks) != TRACK_COUNT or raw.track_genre.nunique() != GENRE_COUNT:
        raise ValueError("Unexpected unique track or genre count")
    return prepared, {
        "dataset_sha256": checksum,
        "raw_rows": len(raw),
        "training_sample_count": len(prepared.tracks),
        "distinct_genres": GENRE_COUNT,
        "preparation_version": PREPARATION_VERSION,
        "prepared_fingerprint": prepared.fingerprint,
    }
