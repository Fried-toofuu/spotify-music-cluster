# Constellation bundle

`entry.js` is the source of the optional Three.js point-constellation view. The
browser loads the prebuilt ESM bundle from the Python package at runtime; Node.js
is not a runtime dependency of the application.

The bundle uses only the verified PCA coordinates and cluster assignments from
the visualization artifact. Glow, point size and camera framing are decorative;
they never move data points or infer genres.

Rebuild from this directory with the pinned toolchain:

```sh
npm install
npm run build
```

The resulting file is `src/spotify_cluster/web/static/constellation.js`. Its MIT
license notice is in `src/spotify_cluster/web/static/THIRD_PARTY_LICENSES.txt`.
The Plotly figure remains the primary scientific Explorer; the constellation is
an optional specialized view with a density fallback when WebGL is unavailable.
