"""Optional HTTP-only Gradio frontend. Importing this package starts no server."""

import os


def _normalize_no_proxy():
    # httpx 0.28, which Gradio builds a client with at import time, rejects
    # bracketed IPv6 entries such as "[::1]" in NO_PROXY; some tooling exports them.
    for name in ("NO_PROXY", "no_proxy"):
        value = os.environ.get(name)
        if value and "[" in value:
            os.environ[name] = ",".join(
                entry[1:-1] if entry.startswith("[") and entry.endswith("]") else entry
                for entry in value.split(",")
            )


_normalize_no_proxy()
