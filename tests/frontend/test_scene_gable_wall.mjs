import assert from 'node:assert/strict';
import { gableWallTriangles } from '../../frontend/scene-viewer-gable-roof.js';

const depthRidge = gableWallTriangles({
  x: 1, y: 2, z: 0, width: 8, depth: 10, height: 6,
  pitchDegrees: 20, overhang: 0.4, ridgeDirection: 'depth',
});
assert.ok(depthRidge);
assert.equal(depthRidge.vertices.length, 18, 'two triangular gable-end wall planes');
assert.deepEqual(depthRidge.vertices.slice(0, 6), [1, 6, 2, 9, 6, 2], 'front gable base stays on host-volume boundary');
assert.equal(depthRidge.vertices[8], 2, 'front apex stays on front facade plane');
assert.equal(depthRidge.vertices[17], 12, 'rear apex stays on rear facade plane');

const widthRidge = gableWallTriangles({
  x: 1, y: 2, z: 0, width: 8, depth: 10, height: 6,
  pitchDegrees: 20, overhang: 0.4, ridgeDirection: 'width',
});
assert.ok(widthRidge);
assert.equal(widthRidge.vertices.length, 18);
assert.equal(widthRidge.vertices[0], 1);
assert.equal(widthRidge.vertices[9], 9);

assert.equal(gableWallTriangles({ x: 0, y: 0, z: 0, width: 8, depth: 10, height: 6, pitchDegrees: null, ridgeDirection: 'depth' }), null,
  'unknown pitch must not invent a gable wall');
assert.equal(gableWallTriangles({ x: 0, y: 0, z: 0, width: 8, depth: 10, height: 6, pitchDegrees: 20, ridgeDirection: null }), null,
  'unknown ridge direction must not invent a gable wall');

console.log('scene gable wall geometry: ok');
