"""Deterministic software-only double; these values are not scientific evidence."""

from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from spotify_cluster.api.app import create_app
from spotify_cluster.config import DEPLOYMENT_V1, F9, LIMITATION


class SoftwareService:
    def __init__(self):
        self.calls = []
        self._metadata = {
            "model_id": "software-fixture-only",
            "deployment_profile": DEPLOYMENT_V1.identifier,
            "number_of_clusters": 2,
            "features": list(F9),
            "training_sample_count": 10,
            "modeling_pca": None,
            "model_origin": "new_deployment_refit",
            "reconstruction_status": "new_deployment_refit",
            "historical_equivalence": "NOT VERIFIED",
            "private_path": "PRIVATE-METADATA-MARKER",
        }
        stats = dict.fromkeys(F9, 0.5)
        self._profiles = {
            "model_id": self._metadata["model_id"],
            "units": "raw F9",
            "std_ddof": 1,
            "singleton_std": 0,
            "clusters": {
                str(i): {
                    "cluster_id": i,
                    "count": 5,
                    "share": 0.5,
                    **{
                        key: stats.copy()
                        for key in ("mean", "median", "std", "q1", "q3", "iqr")
                    },
                }
                for i in range(2)
            },
            "feature_contributions": {
                "definition": "Software fixture only",
                "population": "Software fixture only",
                "between_ss": dict.fromkeys(F9, 1.0),
                "shares": {name: float(name == "instrumentalness") for name in F9},
            },
        }

    @property
    def metadata(self):
        return deepcopy(self._metadata)

    @property
    def profiles(self):
        return deepcopy(self._profiles)

    def _result(self, track):
        label = int(track["instrumentalness"] > 0.5)
        return {
            "cluster_id": label,
            "model_id": self._metadata["model_id"],
            "distances": [0.25, 0.75] if label == 0 else [0.75, 0.25],
            "distance_definition": (
                "Euclidean distance to centroids [0, 1] in fitted RobustScaler space"
            ),
            "profile": deepcopy(self._profiles["clusters"][str(label)]),
            "limitation": LIMITATION,
            **{
                key: self._metadata[key]
                for key in (
                    "reconstruction_status",
                    "deployment_profile",
                    "historical_equivalence",
                )
            },
        }

    def predict_one(self, track):
        self.calls.append(("one", [track]))
        return self._result(track)

    def predict_batch(self, tracks):
        self.calls.append(("batch", tracks))
        return [self._result(track) for track in tracks]


@pytest.fixture
def software_service():
    return SoftwareService()


@pytest.fixture
def api_track():
    return dict(zip(F9, [0.3, 0.6, 0.7, 0.5, 120.0, -8.0, 0.05, 0.0, 0.1], strict=True))


@pytest.fixture
def api_client(software_service, tmp_path):
    application = create_app(tmp_path, service_factory=lambda _: software_service)
    with TestClient(application) as client:
        yield client
