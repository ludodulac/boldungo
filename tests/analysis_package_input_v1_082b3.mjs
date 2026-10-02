import assert from 'node:assert/strict';

import {
  normalizeActiveProjectSnapshotForPackageV1,
} from '../frontend/analysis-package-input-v1.js';


function photo({
  photo_id,
  primary_face,
  original_filename,
  blob,
  note = '',
}) {
  return { photo_id, primary_face, original_filename, blob, note };
}


{
  const frontBlob = new Blob(['front']);
  const left1Blob = new Blob(['left-one']);
  const left2Blob = new Blob(['left-two']);
  const rearBlob = new Blob(['rear']);

  const result = normalizeActiveProjectSnapshotForPackageV1({
    project: { project_id: 'project_real_house' },
    photos: [
      photo({
        photo_id: 'FRONT_001',
        primary_face: 'FRONT',
        original_filename: 'front.jpg',
        blob: frontBlob,
        note: 'Vue principale',
      }),
      photo({
        photo_id: 'LEFT_001',
        primary_face: 'LEFT',
        original_filename: 'left-1.png',
        blob: left1Blob,
        note: 'Première vue gauche',
      }),
      photo({
        photo_id: 'LEFT_002',
        primary_face: 'LEFT',
        original_filename: 'left-2.webp',
        blob: left2Blob,
        note: 'Deuxième vue gauche',
      }),
      photo({
        photo_id: 'REAR_001',
        primary_face: 'REAR',
        original_filename: 'rear.jpeg',
        blob: rearBlob,
        note: '',
      }),
    ],
  });

  assert.equal(result.project_id, 'project_real_house');
  assert.deepEqual(
    result.photos.map(item => item.photo_id),
    ['FRONT_001', 'LEFT_001', 'LEFT_002', 'REAR_001'],
  );
  assert.equal(result.photos.length, 4);
  assert.equal(result.photos[1].photo_id, 'LEFT_001');
  assert.equal(result.photos[2].photo_id, 'LEFT_002');
  assert.strictEqual(result.photos[0].blob, frontBlob);
  assert.strictEqual(result.photos[1].blob, left1Blob);
  assert.strictEqual(result.photos[2].blob, left2Blob);
  assert.strictEqual(result.photos[3].blob, rearBlob);
  assert.equal(result.photos[1].note, 'Première vue gauche');
  assert.equal(result.photos[2].note, 'Deuxième vue gauche');
}


assert.throws(
  () => normalizeActiveProjectSnapshotForPackageV1({
    project: { project_id: 'project_real_house' },
    photos: [
      photo({
        photo_id: 'DETAIL_001',
        primary_face: null,
        original_filename: 'detail.jpg',
        blob: new Blob(['detail']),
        note: 'Détail ancien',
      }),
    ],
  }),
  /primary_face manquant ou invalide/,
);


assert.throws(
  () => normalizeActiveProjectSnapshotForPackageV1({
    project: { project_id: 'project_real_house' },
    photos: [],
  }),
  /Aucune photo active/,
);


assert.throws(
  () => normalizeActiveProjectSnapshotForPackageV1({
    project: null,
    photos: [],
  }),
  /Aucun projet actif/,
);


assert.throws(
  () => normalizeActiveProjectSnapshotForPackageV1({
    project: { project_id: 'project_real_house' },
    photos: [
      photo({
        photo_id: 'LEFT_001',
        primary_face: 'LEFT',
        original_filename: 'left-1.jpg',
        blob: new Blob(['one']),
      }),
      photo({
        photo_id: 'LEFT_001',
        primary_face: 'LEFT',
        original_filename: 'left-2.jpg',
        blob: new Blob(['two']),
      }),
    ],
  }),
  /photo_id dupliqué/,
);


assert.throws(
  () => normalizeActiveProjectSnapshotForPackageV1({
    project: { project_id: 'project_real_house' },
    photos: [
      photo({
        photo_id: 'RIGHT_001',
        primary_face: 'SIDE',
        original_filename: 'right.jpg',
        blob: new Blob(['right']),
      }),
    ],
  }),
  /primary_face manquant ou invalide/,
);


assert.throws(
  () => normalizeActiveProjectSnapshotForPackageV1({
    project: { project_id: 'project_real_house' },
    photos: [
      photo({
        photo_id: 'RIGHT_001',
        primary_face: 'RIGHT',
        original_filename: '',
        blob: new Blob(['right']),
      }),
    ],
  }),
  /original_filename/,
);


assert.throws(
  () => normalizeActiveProjectSnapshotForPackageV1({
    project: { project_id: 'project_real_house' },
    photos: [
      photo({
        photo_id: 'RIGHT_001',
        primary_face: 'RIGHT',
        original_filename: 'right.jpg',
        blob: new Blob([]),
      }),
    ],
  }),
  /blob absent ou vide/,
);

console.log('BOLDUNGO-082B3 package input adapter contract passed');
