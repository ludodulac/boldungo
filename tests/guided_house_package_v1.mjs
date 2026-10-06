import assert from 'node:assert/strict';
import { buildGuidedHousePackageV1, GUIDED_HOUSE_SCHEMA_VERSION } from '../frontend/guided-house-package-v1.js';

const original = new Uint8Array([0x89,0x50,0x4e,0x47,1,2,3,4]);
const snapshot = {
  project: { project_id: 'HOUSE_001', known_front_width: 10.0, general_notes: 'Escalier et terrasse à respecter.' },
  photos: [{ photo_id: 'FRONT_001', primary_face: 'FRONT', original_filename: 'maison-originale.png', blob: new Blob([original], {type:'image/png'}), note: 'Façade avant réelle' }],
};
const built = await buildGuidedHousePackageV1(snapshot, { package_id: 'GUIDED_TEST_001' });
assert.equal(built.guided.schema_version, GUIDED_HOUSE_SCHEMA_VERSION);
assert.equal(built.guided.project_id, 'HOUSE_001');
assert.equal(built.guided.package_id, 'GUIDED_TEST_001');
assert.equal(built.guided.known_front_width, 10.0);
assert.equal(built.guided.general_notes, 'Escalier et terrasse à respecter.');
const photo = built.guided.photos[0];
for (const field of ['photo_id','orientation','description','must_reproduce','do_not_confuse','known_dimensions','connections_to_other_photos','provenance']) assert(Object.hasOwn(photo, field), field);
assert.equal(photo.description, 'Façade avant réelle');
assert.equal(photo.orientation, 'FRONT');
assert.equal(photo.provenance, 'USER_CONFIRMED');
assert.deepEqual(photo.must_reproduce, []);
assert.deepEqual(photo.do_not_confuse, []);
assert.deepEqual(photo.known_dimensions, []);
assert.deepEqual(photo.connections_to_other_photos, []);
assert.deepEqual(built.manifest.photos, [{ photo_id:'FRONT_001', file_path:'photos/FRONT_001.png', original_filename:'maison-originale.png' }]);
const zipBytes = new Uint8Array(await built.blob.arrayBuffer());
let found = false;
for (let i=0;i<=zipBytes.length-original.length;i+=1) {
  if (original.every((byte,j)=>zipBytes[i+j]===byte)) { found=true; break; }
}
assert.equal(found, true, 'original photo bytes must be embedded unchanged');
const empty = await buildGuidedHousePackageV1({ project:{project_id:'P',known_front_width:null,general_notes:''}, photos:[{photo_id:'DETAIL_001',primary_face:null,original_filename:'d.jpg',blob:new Blob([new Uint8Array([1])]),note:''}] }, {package_id:'GUIDED_EMPTY'});
assert.equal(empty.guided.photos[0].orientation, null);
assert.equal(empty.guided.photos[0].description, null);
assert.equal(empty.guided.photos[0].provenance, null);
assert.deepEqual(empty.guided.photos[0].must_reproduce, []);
assert.equal(empty.guided.known_front_width, null);
console.log('guided_house_package_v1 PASS');
