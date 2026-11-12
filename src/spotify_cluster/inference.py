"""Reusable single/batch inference; initialization loads once, prediction never fits."""

from collections.abc import Mapping, Sequence
from copy import deepcopy
from numbers import Real
from pathlib import Path

import numpy as np

from .config import F9, LIMITATION
from .data import validate_matrix
from .model_store import load_bundle


def input_matrix(tracks: Sequence[Mapping[str, Real]]) -> np.ndarray:
    if isinstance(tracks, (str, bytes, Mapping)) or not isinstance(tracks, Sequence):
        raise ValueError("Batch input must be a sequence of feature mappings")
    rows = []
    for track in tracks:
        if not isinstance(track, Mapping) or set(track) != set(F9):
            raise ValueError("Each track must contain exactly the nine F9 features")
        row = []
        for name in F9:
            value = track[name]
            if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
                raise ValueError(f"{name} must be a real number, not boolean or text")
            row.append(value)
        rows.append(row)
    return validate_matrix(np.asarray(rows, dtype=np.float64))


class InferenceService:
    """Load trusted local state with profiles belonging to this model identity."""

    def __init__(self, artifact_dir: Path):
        self._pipeline, self._metadata, self._profiles = load_bundle(artifact_dir)

    @property
    def metadata(self) -> dict:
        """Return a defensive copy of the verified model metadata."""
        return deepcopy(self._metadata)

    @property
    def profiles(self) -> dict:
        """Return aggregate profiles paired with the loaded pipeline."""
        return deepcopy(self._profiles)

    def predict_one(self, track: Mapping[str, Real]) -> dict:
        return self.predict_batch([track])[0]

    def predict_batch(self, tracks: Sequence[Mapping[str, Real]]) -> list[dict]:
        matrix = input_matrix(tracks)
        labels = self._pipeline.predict(matrix)
        distances = self._pipeline.transform(matrix)
        return [
            {
                "cluster_id": int(label),
                "model_id": self._metadata["model_id"],
                "distances": distance.tolist(),
                "distance_definition": (
                    "Euclidean distance to centroids [0, 1] "
                    "in fitted RobustScaler space"
                ),
                "profile": deepcopy(self._profiles["clusters"][str(label)]),
                "limitation": LIMITATION,
                "reconstruction_status": self._metadata["reconstruction_status"],
                "deployment_profile": self._metadata.get("deployment_profile"),
                "historical_equivalence": self._metadata["historical_equivalence"],
            }
            for label, distance in zip(labels, distances, strict=True)
        ]
