/*! Three.js r187 · MIT License · Acoustic Observatory constellation module */
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";


export function createConstellation(options) {
  const { container, points, palette } = options;
  const CLUSTER_COLORS = [palette.cluster_0, palette.cluster_1];
  const onSelect = options.onSelect || (() => {});
  const onHover = options.onHover || (() => {});
  const onReady = options.onReady || (() => {});
  const count = points.x.length;
  if (!count) throw new Error("No sampled points to render");

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(palette.surface_1);

  const positions = new Float32Array(count * 3);
  const colors = new Float32Array(count * 3);
  const pointColors = CLUSTER_COLORS.map((hex) => new THREE.Color(hex));
  const hiddenColor = new THREE.Color(palette.surface_1);
  const visibleClusters = new Set([0, 1]);
  for (let index = 0; index < count; index += 1) {
    const offset = index * 3;
    positions[offset] = points.x[index];
    positions[offset + 1] = points.y[index];
    positions[offset + 2] = points.z[index];
    const color = pointColors[points.cluster[index]] || pointColors[0];
    colors[offset] = color.r;
    colors[offset + 1] = color.g;
    colors[offset + 2] = color.b;
  }
  const baseColors = colors.slice();
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));

  const box = new THREE.Box3().setFromBufferAttribute(
    geometry.getAttribute("position")
  );
  const center = box.getCenter(new THREE.Vector3());
  const size = box.getSize(new THREE.Vector3());
  const extent = Math.max(size.x, size.y, size.z, 1);
  const pointSize = Math.max(0.16, extent * 0.011);

  const spriteCanvas = document.createElement("canvas");
  spriteCanvas.width = 64;
  spriteCanvas.height = 64;
  const spriteContext = spriteCanvas.getContext("2d");
  const glow = spriteContext.createRadialGradient(32, 32, 2, 32, 32, 31);
  glow.addColorStop(0, "rgba(255,255,255,1)");
  glow.addColorStop(0.55, "rgba(255,255,255,0.85)");
  glow.addColorStop(1, "rgba(255,255,255,0)");
  spriteContext.fillStyle = glow;
  spriteContext.fillRect(0, 0, 64, 64);
  const spriteTexture = new THREE.CanvasTexture(spriteCanvas);
  spriteTexture.needsUpdate = true;
  const material = new THREE.PointsMaterial({
    size: pointSize,
    vertexColors: true,
    map: spriteTexture,
    transparent: true,
    alphaTest: 0.02,
    opacity: 0.95,
    sizeAttenuation: true,
    depthWrite: false,
  });
  const cloud = new THREE.Points(geometry, material);
  scene.add(cloud);

  const selectionGeometry = new THREE.BufferGeometry();
  selectionGeometry.setAttribute(
    "position",
    new THREE.BufferAttribute(new Float32Array([0, 0, 0]), 3)
  );
  const selectionMaterial = new THREE.PointsMaterial({
    size: Math.max(0.12, extent * 0.014),
    color: palette.ink,
    transparent: true,
    opacity: 1,
    sizeAttenuation: true,
    depthTest: false,
  });
  const selection = new THREE.Points(selectionGeometry, selectionMaterial);
  selection.visible = false;
  selection.renderOrder = 3;
  scene.add(selection);

  const renderer = new THREE.WebGLRenderer({
    antialias: false,
    alpha: false,
    powerPreference: "high-performance",
  });
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.setClearColor(palette.surface_1, 1);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.domElement.className = "obs-constellation-canvas";
  renderer.domElement.setAttribute("role", "img");
  renderer.domElement.setAttribute(
    "aria-label",
    "Interactive three-dimensional constellation of the sampled PCA coordinates"
  );
  container.appendChild(renderer.domElement);

  const camera = new THREE.PerspectiveCamera(48, 1, 0.1, extent * 40);
  const initial = center
    .clone()
    .add(new THREE.Vector3(extent * 0.55, extent * 0.45, extent * 0.6));
  camera.position.copy(initial);
  camera.lookAt(center);

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.target.copy(center);
  controls.enableDamping = false;
  controls.rotateSpeed = 0.75;
  controls.zoomSpeed = 0.9;
  controls.panSpeed = 0.6;
  controls.minDistance = extent * 0.18;
  controls.maxDistance = extent * 4;

  function render() {
    renderer.render(scene, camera);
  }
  controls.addEventListener("change", render);

  const raycaster = new THREE.Raycaster();
  raycaster.params.Points.threshold = Math.max(0.08, extent * 0.01);
  const pointer = new THREE.Vector2();

  function toNdc(event) {
    const rect = renderer.domElement.getBoundingClientRect();
    pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
  }
  function pick(event) {
    toNdc(event);
    raycaster.setFromCamera(pointer, camera);
    const hits = raycaster.intersectObject(cloud, false);
    for (const hit of hits) {
      if (visibleClusters.has(points.cluster[hit.index])) return hit.index;
    }
    return null;
  }
  function pointerMove(event) {
    if (event.buttons) return;
    const index = pick(event);
    renderer.domElement.style.cursor = index === null ? "grab" : "pointer";
    onHover(index, event.clientX, event.clientY);
  }
  function pointerLeave() {
    renderer.domElement.style.cursor = "grab";
    onHover(null, 0, 0);
  }
  let down = null;
  function pointerDown(event) {
    down = { x: event.clientX, y: event.clientY };
  }
  function pointerUp(event) {
    if (!down) return;
    const moved = Math.hypot(event.clientX - down.x, event.clientY - down.y);
    down = null;
    if (moved > 6) return;
    const index = pick(event);
    if (index === null) return;
    select(index);
    onSelect(index);
  }
  renderer.domElement.addEventListener("pointermove", pointerMove);
  renderer.domElement.addEventListener("pointerleave", pointerLeave);
  renderer.domElement.addEventListener("pointerdown", pointerDown);
  renderer.domElement.addEventListener("pointerup", pointerUp);

  let selectedIndex = null;

  function select(index) {
    if (!Number.isInteger(index) || index < 0 || index >= count) return;
    selectedIndex = index;
    const attribute = selectionGeometry.getAttribute("position");
    attribute.setXYZ(0, points.x[index], points.y[index], points.z[index]);
    attribute.needsUpdate = true;
    selection.visible = visibleClusters.has(points.cluster[index]);
    render();
  }

  function clearSelection() {
    selectedIndex = null;
    selection.visible = false;
    render();
  }

  function setVisibleClusters(labels) {
    visibleClusters.clear();
    for (const label of labels || []) {
      if (label === 0 || label === 1) visibleClusters.add(label);
    }
    if (!visibleClusters.size) visibleClusters.add(0);
    for (let index = 0; index < count; index += 1) {
      const offset = index * 3;
      const source = visibleClusters.has(points.cluster[index])
        ? baseColors
        : null;
      colors[offset] = source ? source[offset] : hiddenColor.r;
      colors[offset + 1] = source ? source[offset + 1] : hiddenColor.g;
      colors[offset + 2] = source ? source[offset + 2] : hiddenColor.b;
    }
    geometry.getAttribute("color").needsUpdate = true;
    selection.visible =
      selectedIndex !== null &&
      visibleClusters.has(points.cluster[selectedIndex]);
    render();
  }

  function resize() {
    const width = container.clientWidth || 600;
    const height = container.clientHeight || 400;
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    renderer.setSize(width, height, false);
    render();
  }

  function resetCamera() {
    camera.position.copy(initial);
    controls.target.copy(center);
    controls.update();
    render();
  }

  function projectPoint(index) {
    if (!Number.isInteger(index) || index < 0 || index >= count) return null;
    const vector = new THREE.Vector3(
      points.x[index],
      points.y[index],
      points.z[index]
    ).project(camera);
    return {
      x: (vector.x * 0.5 + 0.5) * renderer.domElement.clientWidth,
      y: (-vector.y * 0.5 + 0.5) * renderer.domElement.clientHeight,
    };
  }

  const observer = new ResizeObserver(resize);
  observer.observe(container);
  resize();
  render();
  onReady();

  function dispose() {
    observer.disconnect();
    renderer.domElement.removeEventListener("pointermove", pointerMove);
    renderer.domElement.removeEventListener("pointerleave", pointerLeave);
    renderer.domElement.removeEventListener("pointerdown", pointerDown);
    renderer.domElement.removeEventListener("pointerup", pointerUp);
    controls.dispose();
    geometry.dispose();
    material.dispose();
    selectionGeometry.dispose();
    selectionMaterial.dispose();
    spriteTexture.dispose();
    renderer.dispose();
    if (renderer.forceContextLoss) renderer.forceContextLoss();
    if (renderer.domElement.parentNode) {
      renderer.domElement.parentNode.removeChild(renderer.domElement);
    }
  }

  return { dispose, resetCamera, resize, select, clearSelection, setVisibleClusters, projectPoint };
}
