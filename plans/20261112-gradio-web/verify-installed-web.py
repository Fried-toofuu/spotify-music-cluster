"""Run from outside checkout with the isolated installed-wheel interpreter."""

import sys

import spotify_cluster
from spotify_cluster.web.app import create_app, launch_options

assert "site-packages" in spotify_cluster.__file__
assert not any(
    "spotify_cluster." + n in sys.modules
    for n in ("model_store", "inference", "training", "data")
)
app = create_app()
assert len([c for c in app.config["components"] if c["type"] == "tabitem"]) == 4
options = launch_options()
assert options["share"] is False and options["run_history"] is False
assert options["server_name"] == "127.0.0.1" and options["server_port"] == 7860
assert options["allowed_paths"] == []
assert options["show_error"] is False
print("PASS: installed wheel imports and constructs four tabs outside source checkout")
