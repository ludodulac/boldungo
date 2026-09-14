import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { gableRoofTriangles } from './scene-viewer-gable-roof.js';

const canvas = document.querySelector('#viewer');
const messageEl = document.querySelector('#message');
const summary = document.querySelector('#scene-summary');
const roofNote = document.querySelector('#roof-note');
const resetButton = document.querySelector('#reset-view');
const frontButton = document.querySelector('#view-front');
const rearButton = document.querySelector('#view-rear');
const leftButton = document.querySelector('#view-left');
const rightButton = document.querySelector('#view-right');

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x101827);
const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
scene.add(new THREE.HemisphereLight(0xffffff, 0x263247, 2.4));
const light = new THREE.DirectionalLight(0xfff3dd, 2.8);
light.position.set(15, 24, 18);
scene.add(light);
const grid = new THREE.GridHelper(60, 60, 0x53627c, 0x27344b);
scene.add(grid);
const group = new THREE.Group();
group.scale.z = -1;
scene.add(group);

const wallMaterial = new THREE.MeshStandardMaterial({ color: 0xd9d2c3, roughness: 0.65, transparent: true, opacity: 0.88 });
const openingMaterial = new THREE.MeshStandardMaterial({ color: 0x243447, roughness: 0.3 });
const exactRoofMaterial = new THREE.MeshStandardMaterial({ color: 0x5f646b, roughness: 0.65, side: THREE.DoubleSide });
const uncertainRoofMaterial = new THREE.MeshStandardMaterial({ color: 0xd59a55, transparent: true, opacity: 0.32, side: THREE.DoubleSide, depthWrite: false });
const timberMaterial = new THREE.MeshStandardMaterial({ color: 0x9b7045, roughness: 0.72 });
const concreteMaterial = new THREE.MeshStandardMaterial({ color: 0xa9aaa5, roughness: 0.78 });
const genericExteriorMaterial = new THREE.MeshStandardMaterial({ color: 0x8f918d, roughness: 0.74 });
const edgeMaterial = new THREE.LineBasicMaterial({ color: 0x1a202c, transparent: true, opacity: 0.45 });
const observedTerrainMaterial = new THREE.LineDashedMaterial({ color: 0xe4c468, dashSize: 0.28, gapSize: 0.18, transparent: true, opacity: 0.9 });

let currentScene = null;
const terrainNotes = [];

function metric(value) { return Number(value?.value ?? value); }
function knownNumber(value) { return value !== null && value !== undefined && Number.isFinite(Number(value)); }
function addEdges(mesh) { mesh.add(new THREE.LineSegments(new THREE.EdgesGeometry(mesh.geometry), edgeMaterial)); }
function exteriorMaterial(kind) {
  if (kind === 'timber') return timberMaterial;
  if (kind === 'concrete') return concreteMaterial;
  return genericExteriorMaterial;
}

function volumeById(id) { return currentScene?.volumes?.find(item => item.id === id) ?? null; }

function renderVolumes() {
  for (const volume of currentScene.volumes ?? []) {
    const width = metric(volume.width), depth = metric(volume.depth), height = metric(volume.height);
    if (![width, depth, height].every(Number.isFinite)) continue;
    const geometry = new THREE.BoxGeometry(width, height, depth);
    const mesh = new THREE.Mesh(geometry, wallMaterial);
    addEdges(mesh);
    const p = volume.position ?? { x: 0, y: 0, z: 0 };
    mesh.position.set(Number(p.x) + width / 2, Number(p.z) + height / 2, Number(p.y) + depth / 2);
    group.add(mesh);
  }
}

function renderOpenings() {
  for (const opening of currentScene.openings ?? []) {
    const volume = volumeById(opening.volume_id);
    if (!volume) continue;
    const width = metric(volume.width), depth = metric(volume.depth), height = metric(volume.height);
    if (![width, depth, height].every(Number.isFinite)) continue;
    const ow = Number(opening.width), oh = Number(opening.height), ox = Number(opening.offset_horizontal), oz = Number(opening.offset_vertical);
    if (![ow, oh, ox, oz].every(Number.isFinite)) continue;
    const p = volume.position ?? { x: 0, y: 0, z: 0 };
    const thickness = 0.035;
    let geometry, x, y, z;
    if (opening.facade === 'front' || opening.facade === 'rear') {
      geometry = new THREE.BoxGeometry(ow, oh, thickness);
      x = Number(p.x) + ox + ow / 2;
      y = Number(p.z) + oz + oh / 2;
      z = Number(p.y) + (opening.facade === 'front' ? -thickness : depth + thickness);
    } else {
      geometry = new THREE.BoxGeometry(thickness, oh, ow);
      x = Number(p.x) + (opening.facade === 'left' ? -thickness : width + thickness);
      y = Number(p.z) + oz + oh / 2;
      z = Number(p.y) + ox + ow / 2;
    }
    const mesh = new THREE.Mesh(geometry, openingMaterial);
    mesh.position.set(x, y, z);
    group.add(mesh);
  }
}

function renderPlatforms() {
  for (const platform of currentScene.platforms ?? []) {
    const p = platform.position;
    const width = Number(platform.width), depth = Number(platform.depth), thickness = Number(platform.thickness);
    if (!p || ![Number(p.x), Number(p.y), Number(p.z), width, depth, thickness].every(Number.isFinite)) continue;
    const geometry = new THREE.BoxGeometry(width, thickness, depth);
    const mesh = new THREE.Mesh(geometry, exteriorMaterial(platform.material));
    addEdges(mesh);
    mesh.position.set(Number(p.x) + width / 2, Number(p.z) + thickness / 2, Number(p.y) + depth / 2);
    mesh.userData.architecturalObjectId = platform.id;
    group.add(mesh);
    // edge_treatment may say that a railing exists, but without explicit edge geometry
    // the preview intentionally does not guess which sides receive posts or rails.
  }
}

function renderPartialWallSegments() {
  for (const wall of currentScene.partial_wall_segments ?? []) {
    const start = wall.start, end = wall.end;
    const height = metric(wall.height);
    if (!start || !end || !knownNumber(height)) continue;
    const values = [start.x, start.y, start.z, end.x, end.y, end.z].map(Number);
    if (!values.every(Number.isFinite)) continue;
    const [sx, sy, sz, ex, ey, ez] = values;
    const vertices = new Float32Array([
      sx, sz, sy,
      ex, ez, ey,
      ex, ez + height, ey,
      sx, sz, sy,
      ex, ez + height, ey,
      sx, sz + height, sy,
    ]);
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.BufferAttribute(vertices, 3));
    geometry.computeVertexNormals();
    const base = exteriorMaterial(wall.material);
    const material = base.clone();
    material.side = THREE.DoubleSide;
    const mesh = new THREE.Mesh(geometry, material);
    mesh.userData.architecturalObjectId = wall.id;
    mesh.userData.architecturalThickness = metric(wall.thickness);
    mesh.userData.renderingConvention = 'zero-thickness visible plane when architectural thickness is unknown';
    addEdges(mesh);
    group.add(mesh);
  }
}

function renderStairs() {
  for (const stair of currentScene.stairs ?? []) {
    const start = stair.start, end = stair.end;
    const width = Number(stair.width);
    if (!start || !end || ![Number(start.x), Number(start.y), Number(start.z), Number(end.x), Number(end.y), Number(end.z), width].every(Number.isFinite)) continue;
    const from = new THREE.Vector3(Number(start.x), Number(start.z), Number(start.y));
    const to = new THREE.Vector3(Number(end.x), Number(end.z), Number(end.y));
    const delta = to.clone().sub(from);
    const length = delta.length();
    if (!(length > 0)) continue;
    const thickness = 0.16;
    const geometry = new THREE.BoxGeometry(width, thickness, length);
    const mesh = new THREE.Mesh(geometry, exteriorMaterial(stair.material));
    addEdges(mesh);
    mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), delta.clone().normalize());
    mesh.position.copy(from).add(to).multiplyScalar(0.5);
    mesh.userData.architecturalObjectId = stair.id;
    group.add(mesh);
  }
}

function facadeGroundEndpoints(volume, facade) {
  const width = metric(volume.width), depth = metric(volume.depth);
  if (![width, depth].every(Number.isFinite)) return null;
  const p = volume.position ?? { x: 0, y: 0, z: 0 };
  const x = Number(p.x), y = Number(p.y), z = Number(p.z) + 0.035;
  if (![x, y, z].every(Number.isFinite)) return null;
  if (facade === 'right') return [new THREE.Vector3(x + width + 0.06, z, y), new THREE.Vector3(x + width + 0.06, z, y + depth)];
  if (facade === 'left') return [new THREE.Vector3(x - 0.06, z, y), new THREE.Vector3(x - 0.06, z, y + depth)];
  if (facade === 'front') return [new THREE.Vector3(x, z, y - 0.06), new THREE.Vector3(x + width, z, y - 0.06)];
  if (facade === 'rear') return [new THREE.Vector3(x, z, y + depth + 0.06), new THREE.Vector3(x + width, z, y + depth + 0.06)];
  return null;
}

function renderTerrain() {
  const profiles = currentScene.terrain?.profiles ?? [];
  const host = currentScene.volumes?.[0];
  if (!host) return;
  for (const profile of profiles) {
    const hasMetricProfile = [profile.start_elevation, profile.end_elevation, profile.outward_extent].every(knownNumber);
    if (hasMetricProfile) {
      terrainNotes.push(`Terrain ${profile.facade} : profil métrique disponible ; surface détaillée pas encore rendue dans cet aperçu.`);
      continue;
    }
    const endpoints = facadeGroundEndpoints(host, profile.facade);
    if (!endpoints) continue;
    const geometry = new THREE.BufferGeometry().setFromPoints(endpoints);
    const marker = new THREE.Line(geometry, observedTerrainMaterial);
    marker.computeLineDistances();
    marker.userData.terrainGradeStatus = 'observed-unmetered';
    marker.userData.facade = profile.facade;
    group.add(marker);
    terrainNotes.push(`Terrain ${profile.facade} : pente observée mais non métrée ; le trait pointillé localise seulement la façade concernée, sans inventer d’angle ni d’amplitude.`);
  }
}

function shedRoofPlane(volume, roof, degrees, material) {
  const width = metric(volume.width), depth = metric(volume.depth), height = metric(volume.height);
  if (![width, depth, height, degrees].every(Number.isFinite) || !roof.down_slope_direction) return null;
  const direction = roof.down_slope_direction;
  const alongDepth = direction === 'front' || direction === 'rear';
  const run = alongDepth ? depth : width;
  const cross = alongDepth ? width : depth;
  const rise = Math.tan(THREE.MathUtils.degToRad(degrees)) * run;
  const geometry = new THREE.PlaneGeometry(cross, Math.hypot(run, rise));
  const mesh = new THREE.Mesh(geometry, material);
  const p = volume.position ?? { x: 0, y: 0, z: 0 };
  mesh.rotation.x = -Math.PI / 2;
  if (alongDepth) {
    mesh.rotation.x += (direction === 'rear' ? -1 : 1) * THREE.MathUtils.degToRad(degrees);
    mesh.position.set(Number(p.x) + width / 2, Number(p.z) + height + rise / 2, Number(p.y) + depth / 2);
  } else {
    mesh.rotation.x = -Math.PI / 2;
    mesh.rotation.y = (direction === 'right' ? -1 : 1) * THREE.MathUtils.degToRad(degrees);
    mesh.position.set(Number(p.x) + width / 2, Number(p.z) + height + rise / 2, Number(p.y) + depth / 2);
  }
  return mesh;
}

function gableRoofMesh(volume, roof, material) {
  const width = metric(volume.width), depth = metric(volume.depth), height = metric(volume.height);
  const p = volume.position ?? { x: 0, y: 0, z: 0 };
  if (![width, depth, height, Number(p.x), Number(p.y), Number(p.z)].every(Number.isFinite)) return null;
  if (!knownNumber(roof.pitch_degrees) || !roof.ridge_direction) return null;
  const data = gableRoofTriangles({
    x: Number(p.x),
    y: Number(p.y),
    z: Number(p.z),
    width,
    depth,
    height,
    pitchDegrees: Number(roof.pitch_degrees),
    overhang: Number(roof.overhang ?? 0),
    ridgeDirection: roof.ridge_direction,
  });
  if (!data) return null;
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.BufferAttribute(new Float32Array(data.vertices), 3));
  geometry.computeVertexNormals();
  const mesh = new THREE.Mesh(geometry, material);
  mesh.userData.architecturalObjectId = roof.id;
  mesh.userData.ridgeDirection = data.ridgeDirection;
  mesh.userData.ridgeElevation = data.ridgeElevation;
  addEdges(mesh);
  return mesh;
}

function renderRoofs() {
  const notes = [];
  for (const roof of currentScene.roofs ?? []) {
    const volume = volumeById(roof.volume_id);
    if (!volume) continue;
    if (roof.type === 'flat') {
      const width = metric(volume.width), depth = metric(volume.depth), height = metric(volume.height);
      const geometry = new THREE.PlaneGeometry(width, depth);
      const mesh = new THREE.Mesh(geometry, exactRoofMaterial);
      mesh.rotation.x = -Math.PI / 2;
      const p = volume.position ?? { x: 0, y: 0, z: 0 };
      mesh.position.set(Number(p.x) + width / 2, Number(p.z) + height + 0.02, Number(p.y) + depth / 2);
      group.add(mesh);
      notes.push(`${roof.id} : toit plat.`);
      continue;
    }
    if (roof.type === 'gable') {
      const mesh = gableRoofMesh(volume, roof, exactRoofMaterial);
      if (mesh) {
        group.add(mesh);
        notes.push(`${roof.id} : toit à deux pans, faîtage ${roof.ridge_direction}, pente ${roof.pitch_degrees}°.`);
      } else {
        const unknowns = [];
        if (!knownNumber(roof.pitch_degrees)) unknowns.push('pente');
        if (!roof.ridge_direction) unknowns.push('direction de faîtage');
        notes.push(`${roof.id} : ${unknowns.join(' et ') || 'géométrie'} inconnue, aucun toit à deux pans arbitraire n’est dessiné.`);
      }
      continue;
    }
    if (roof.type !== 'shed') {
      notes.push(`${roof.id} : type ${roof.type}, aperçu détaillé pas encore pris en charge.`);
      continue;
    }
    if (knownNumber(roof.pitch_degrees) && roof.down_slope_direction) {
      const mesh = shedRoofPlane(volume, roof, Number(roof.pitch_degrees), exactRoofMaterial);
      if (mesh) group.add(mesh);
      notes.push(`${roof.id} : pente ${roof.pitch_degrees}° vers ${roof.down_slope_direction}.`);
      continue;
    }
    const range = roof.pitch_range_degrees;
    if (range && knownNumber(range.min_degrees) && knownNumber(range.max_degrees) && roof.down_slope_direction) {
      const minMesh = shedRoofPlane(volume, roof, Number(range.min_degrees), uncertainRoofMaterial);
      const maxMesh = shedRoofPlane(volume, roof, Number(range.max_degrees), uncertainRoofMaterial);
      if (minMesh) group.add(minMesh);
      if (maxMesh) group.add(maxMesh);
      notes.push(`${roof.id} : pente encore incertaine entre ${range.min_degrees}° et ${range.max_degrees}, descente vers ${roof.down_slope_direction}. Les deux plans transparents montrent les limites, pas un angle choisi.`);
    } else {
      const unknowns = [];
      if (!knownNumber(roof.pitch_degrees) && !range) unknowns.push('pente');
      if (!roof.down_slope_direction) unknowns.push('direction de descente');
      notes.push(`${roof.id} : ${unknowns.join(' et ') || 'géométrie'} inconnue, aucun plan de toiture arbitraire n’est dessiné.`);
    }
  }
  roofNote.textContent = notes.join(' ') || 'Aucune toiture décrite.';
}

function modelFrame() {
  const box = new THREE.Box3().setFromObject(group);
  if (box.isEmpty()) return null;
  return { size: box.getSize(new THREE.Vector3()), center: box.getCenter(new THREE.Vector3()) };
}
function frame(view = 'perspective') {
  const info = modelFrame(); if (!info) return;
  const d = Math.max(info.size.x, info.size.y, info.size.z, 1) * 1.9;
  const directions = { front: new THREE.Vector3(0, 0, 1), rear: new THREE.Vector3(0, 0, -1), left: new THREE.Vector3(-1, 0, 0), right: new THREE.Vector3(1, 0, 0), perspective: new THREE.Vector3(0.9, 0.7, 1.1) };
  controls.target.copy(info.center);
  camera.position.copy(info.center).addScaledVector(directions[view].normalize(), d);
  camera.lookAt(info.center); controls.update();
}

function updateSummary() {
  const roof = currentScene.roofs?.[0];
  const roofLabel = knownNumber(roof?.pitch_degrees) ? `${roof.type} · ${roof.pitch_degrees}°` : roof?.pitch_range_degrees ? `${roof.type} · ${roof.pitch_range_degrees.min_degrees}–${roof.pitch_range_degrees.max_degrees}°` : roof?.type ?? '—';
  const values = [currentScene.name ?? currentScene.id ?? '—', String(currentScene.volumes?.length ?? 0), String(currentScene.openings?.length ?? 0), roofLabel];
  [...summary.querySelectorAll('dd')].forEach((node, index) => { node.textContent = values[index] ?? '—'; });
}

function loadScene() {
  const keys = ['brickhouse.previewArchitecturalScene', 'brickhouse.pendingSceneValidation', 'brickhouse.lastSceneSurveyValidation'];
  for (const key of keys) {
    try {
      const raw = localStorage.getItem(key); if (!raw) continue;
      const value = JSON.parse(raw);
      const candidate = value?.scene ?? value;
      if (candidate?.schema_version === '0.2' && Array.isArray(candidate.volumes)) return candidate;
    } catch { /* try next source */ }
  }
  return null;
}

currentScene = loadScene();
if (!currentScene) {
  messageEl.textContent = 'Aucune ArchitecturalScene disponible. Revenez au parcours Photos et validez d’abord la reconstruction.';
} else {
  renderVolumes(); renderOpenings(); renderPlatforms(); renderPartialWallSegments(); renderStairs(); renderTerrain(); renderRoofs(); updateSummary(); frame();
  const exteriorCount = (currentScene.platforms?.length ?? 0) + (currentScene.partial_wall_segments?.length ?? 0) + (currentScene.stairs?.length ?? 0);
  const baseMessage = exteriorCount
    ? `Aperçu architectural chargé, avec ${exteriorCount} élément(s) extérieur(s) métriquement défini(s). Les détails non mesurés ne sont pas inventés.`
    : 'Aperçu architectural chargé. Cette vue ne remplace pas la validation nécessaire avant la construction LEGO.';
  messageEl.textContent = [baseMessage, ...terrainNotes].join(' ');
}

resetButton.addEventListener('click', () => frame('perspective'));
frontButton.addEventListener('click', () => frame('front'));
rearButton.addEventListener('click', () => frame('rear'));
leftButton.addEventListener('click', () => frame('left'));
rightButton.addEventListener('click', () => frame('right'));

function resize() {
  const width = canvas.clientWidth, height = canvas.clientHeight;
  if (canvas.width !== width || canvas.height !== height) {
    renderer.setSize(width, height, false);
    camera.aspect = width / Math.max(height, 1);
    camera.updateProjectionMatrix();
  }
}
function animate() { resize(); controls.update(); renderer.render(scene, camera); requestAnimationFrame(animate); }
animate();