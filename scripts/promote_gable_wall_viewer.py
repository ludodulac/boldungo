#!/usr/bin/env python3
from pathlib import Path

path = Path(__file__).resolve().parents[1] / 'frontend' / 'scene-viewer.js'
src = path.read_text(encoding='utf-8')
old_import = "import { gableRoofTriangles } from './scene-viewer-gable-roof.js';"
new_import = "import { gableRoofTriangles, gableWallTriangles } from './scene-viewer-gable-roof.js';"
if new_import not in src:
    if old_import not in src:
        raise RuntimeError('gable roof import anchor not found')
    src = src.replace(old_import, new_import, 1)

helper = r'''
function gableWallMesh(volume, roof) {
  const width = metric(volume.width), depth = metric(volume.depth), height = metric(volume.height);
  const p = volume.position ?? { x: 0, y: 0, z: 0 };
  if (![width, depth, height, Number(p.x), Number(p.y), Number(p.z)].every(Number.isFinite)) return null;
  if (!knownNumber(roof.pitch_degrees) || !roof.ridge_direction) return null;
  const data = gableWallTriangles({
    x: Number(p.x), y: Number(p.y), z: Number(p.z), width, depth, height,
    pitchDegrees: Number(roof.pitch_degrees), overhang: Number(roof.overhang ?? 0), ridgeDirection: roof.ridge_direction,
  });
  if (!data) return null;
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.BufferAttribute(new Float32Array(data.vertices), 3));
  geometry.computeVertexNormals();
  const material = wallMaterial.clone();
  material.side = THREE.DoubleSide;
  const mesh = new THREE.Mesh(geometry, material);
  mesh.userData.architecturalObjectId = roof.volume_id;
  mesh.userData.renderingConvention = 'gable-end wall plane derived from known volume and gable roof geometry';
  addEdges(mesh);
  return mesh;
}
'''
marker = '\nfunction renderRoofs() {'
if 'function gableWallMesh(volume, roof)' not in src:
    if marker not in src:
        raise RuntimeError('renderRoofs anchor not found')
    src = src.replace(marker, '\n' + helper + marker, 1)

old_block = """    if (roof.type === 'gable') {\n      const mesh = gableRoofMesh(volume, roof, exactRoofMaterial);\n      if (mesh) {\n        group.add(mesh);"""
new_block = """    if (roof.type === 'gable') {\n      const mesh = gableRoofMesh(volume, roof, exactRoofMaterial);\n      if (mesh) {\n        const gableWall = gableWallMesh(volume, roof);\n        if (gableWall) group.add(gableWall);\n        group.add(mesh);"""
if new_block not in src:
    if old_block not in src:
        raise RuntimeError('gable render anchor not found')
    src = src.replace(old_block, new_block, 1)

path.write_text(src, encoding='utf-8')
print(path)
