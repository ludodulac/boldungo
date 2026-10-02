import assert from 'node:assert/strict';
import { writeFile } from 'node:fs/promises';

import { buildAnalysisPackageZipV1 } from '../frontend/analysis-package-zip-v1.js';


const outputPath = process.argv[2];
if (!outputPath) throw new Error('output path required');

const frontBytes = new Uint8Array([0xff, 0xd8, 0x46, 0x52, 0x4f, 0x4e, 0x54, 0xff, 0xd9]);
const leftBytes = new Uint8Array([0x89, 0x50, 0x4e, 0x47, 0x4c, 0x45, 0x46, 0x54]);
const rightBytes = new Uint8Array([0x52, 0x49, 0x46, 0x46, 0x57, 0x45, 0x42, 0x50]);

const packageInput = {
  project_id: 'PROJECT_A',
  photos: [
    {
      photo_id: 'FRONT_001',
      primary_face: 'FRONT',
      original_filename: 'facade-originale.jpg',
      blob: new Blob([frontBytes], { type: 'image/jpeg' }),
      note: 'Vue de face',
    },
    {
      photo_id: 'LEFT_001',
      primary_face: 'LEFT',
      original_filename: 'gauche-originale.PNG',
      blob: new Blob([leftBytes], { type: 'image/png' }),
      note: null,
    },
    {
      photo_id: 'RIGHT_001',
      primary_face: 'RIGHT',
      original_filename: 'droite.webp',
      blob: new Blob([rightBytes], { type: 'image/webp' }),
      note: 'Angle légèrement oblique',
    },
  ],
};

const promptText = 'PROMPT EXACT\nSans transformation.';

const built = await buildAnalysisPackageZipV1({
  package_input: packageInput,
  agent_id: 'SOPHIE',
  agent_display_name: 'Sophie',
  round_id: 'R001',
  package_id: 'PKG_550e8400-e29b-41d4-a716-446655440000',
  prompt_text: promptText,
});

assert.equal(built.filename, 'BOLDUNGO_PROJECT_A_SOPHIE_R001.zip');
assert(built.blob instanceof Blob);
assert.equal(built.blob.type, 'application/zip');
assert(built.blob.size > 0);

await writeFile(outputPath, new Uint8Array(await built.blob.arrayBuffer()));

await assert.rejects(
  () => buildAnalysisPackageZipV1({
    package_input: null,
    agent_id: 'SOPHIE',
    agent_display_name: 'Sophie',
    round_id: 'R001',
    package_id: 'PKG_550e8400-e29b-41d4-a716-446655440000',
    prompt_text: promptText,
  }),
  /package_input invalide/,
);

await assert.rejects(
  () => buildAnalysisPackageZipV1({
    package_input: { project_id: 'PROJECT_A', photos: [] },
    agent_id: 'SOPHIE',
    agent_display_name: 'Sophie',
    round_id: 'R001',
    package_id: 'PKG_550e8400-e29b-41d4-a716-446655440000',
    prompt_text: promptText,
  }),
  /aucune photo/,
);

await assert.rejects(
  () => buildAnalysisPackageZipV1({
    package_input: packageInput,
    agent_id: 'SOPHIE SPACE',
    agent_display_name: 'Sophie',
    round_id: 'R001',
    package_id: 'PKG_550e8400-e29b-41d4-a716-446655440000',
    prompt_text: promptText,
  }),
  /agent_id invalide/,
);

await assert.rejects(
  () => buildAnalysisPackageZipV1({
    package_input: packageInput,
    agent_id: 'SOPHIE',
    agent_display_name: 'Sophie',
    round_id: 'ROUND1',
    package_id: 'PKG_550e8400-e29b-41d4-a716-446655440000',
    prompt_text: promptText,
  }),
  /round_id invalide/,
);

await assert.rejects(
  () => buildAnalysisPackageZipV1({
    package_input: packageInput,
    agent_id: 'SOPHIE',
    agent_display_name: 'Sophie',
    round_id: 'R001',
    package_id: 'PKG_NOT_VALID',
    prompt_text: promptText,
  }),
  /package_id invalide/,
);

await assert.rejects(
  () => buildAnalysisPackageZipV1({
    package_input: {
      project_id: 'PROJECT_A',
      photos: [{
        photo_id: 'FRONT_001',
        primary_face: 'FRONT',
        original_filename: 'facade',
        blob: new Blob([frontBytes]),
        note: null,
      }],
    },
    agent_id: 'SOPHIE',
    agent_display_name: 'Sophie',
    round_id: 'R001',
    package_id: 'PKG_550e8400-e29b-41d4-a716-446655440000',
    prompt_text: promptText,
  }),
  /extension originale impossible/,
);

await assert.rejects(
  () => buildAnalysisPackageZipV1({
    package_input: {
      project_id: 'PROJECT_A',
      photos: [{
        photo_id: 'FRONT_001',
        primary_face: 'FRONT',
        original_filename: 'facade.jpg',
        blob: new Blob([]),
        note: null,
      }],
    },
    agent_id: 'SOPHIE',
    agent_display_name: 'Sophie',
    round_id: 'R001',
    package_id: 'PKG_550e8400-e29b-41d4-a716-446655440000',
    prompt_text: promptText,
  }),
  /Blob absent ou vide/,
);

await assert.rejects(
  () => buildAnalysisPackageZipV1({
    package_input: {
      project_id: 'PROJECT_A',
      photos: [
        {
          photo_id: 'LEFT_001',
          primary_face: 'LEFT',
          original_filename: 'one.jpg',
          blob: new Blob([leftBytes]),
          note: null,
        },
        {
          photo_id: 'LEFT_001',
          primary_face: 'LEFT',
          original_filename: 'two.png',
          blob: new Blob([leftBytes]),
          note: null,
        },
      ],
    },
    agent_id: 'SOPHIE',
    agent_display_name: 'Sophie',
    round_id: 'R001',
    package_id: 'PKG_550e8400-e29b-41d4-a716-446655440000',
    prompt_text: promptText,
  }),
  /photo_id dupliqué/,
);

console.log(JSON.stringify({
  filename: built.filename,
  prompt_text: promptText,
  photo_hex: {
    FRONT_001: Buffer.from(frontBytes).toString('hex'),
    LEFT_001: Buffer.from(leftBytes).toString('hex'),
    RIGHT_001: Buffer.from(rightBytes).toString('hex'),
  },
}));
