import { getActiveProjectSnapshot } from './project-photo-store.js';

export const GUIDED_HOUSE_SCHEMA_VERSION = 'boldungo.guided-house-package.v1';
const encoder = new TextEncoder();

function requiredString(value, label) {
  if (typeof value !== 'string' || !value.trim()) throw new Error(`${label} requis`);
  return value;
}

function optionalString(value) {
  return typeof value === 'string' && value.length ? value : null;
}

function extension(filename) {
  const match = requiredString(filename, 'original_filename').match(/\.[A-Za-z0-9]+$/);
  if (!match) throw new Error(`extension originale impossible à déterminer: ${filename}`);
  return match[0];
}

function crcTable() {
  const table = new Uint32Array(256);
  for (let n = 0; n < 256; n += 1) {
    let c = n;
    for (let k = 0; k < 8; k += 1) c = (c & 1) ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    table[n] = c >>> 0;
  }
  return table;
}
const CRC_TABLE = crcTable();
function crc32(bytes) {
  let crc = 0xffffffff;
  for (const byte of bytes) crc = CRC_TABLE[(crc ^ byte) & 0xff] ^ (crc >>> 8);
  return (crc ^ 0xffffffff) >>> 0;
}
function concat(chunks) {
  const result = new Uint8Array(chunks.reduce((n, chunk) => n + chunk.length, 0));
  let offset = 0;
  for (const chunk of chunks) { result.set(chunk, offset); offset += chunk.length; }
  return result;
}
function u16(value) { const b = new Uint8Array(2); new DataView(b.buffer).setUint16(0, value, true); return b; }
function u32(value) { const b = new Uint8Array(4); new DataView(b.buffer).setUint32(0, value >>> 0, true); return b; }
function zip(entries) {
  const locals = []; const centrals = []; let offset = 0;
  for (const entry of entries) {
    const name = encoder.encode(entry.name); const data = entry.bytes; const crc = crc32(data);
    const local = concat([u32(0x04034b50),u16(20),u16(0x0800),u16(0),u16(0),u16(0x0021),u32(crc),u32(data.length),u32(data.length),u16(name.length),u16(0),name]);
    locals.push(local, data);
    centrals.push(concat([u32(0x02014b50),u16(20),u16(20),u16(0x0800),u16(0),u16(0),u16(0x0021),u32(crc),u32(data.length),u32(data.length),u16(name.length),u16(0),u16(0),u16(0),u16(0),u32(0),u32(offset),name]));
    offset += local.length + data.length;
  }
  const central = concat(centrals);
  return concat([...locals, central, u32(0x06054b50),u16(0),u16(0),u16(entries.length),u16(entries.length),u32(central.length),u32(offset),u16(0)]);
}

export function createGuidedPackageId(projectId, photos) {
  const fingerprint = photos.map(p => `${p.photo_id}:${p.original_filename}:${p.blob.size}`).join('|');
  let hash = 2166136261;
  for (const byte of encoder.encode(`${projectId}|${fingerprint}`)) { hash ^= byte; hash = Math.imul(hash, 16777619); }
  return `GUIDED_${projectId}_${(hash >>> 0).toString(16).padStart(8, '0')}`;
}

export async function buildGuidedHousePackageV1(snapshot, { package_id = null } = {}) {
  const project = snapshot?.project;
  const photos = Array.isArray(snapshot?.photos) ? snapshot.photos : [];
  if (!project) throw new Error('Aucun projet actif');
  const projectId = requiredString(project.project_id, 'project_id');
  if (!photos.length) throw new Error('Aucune photo active');
  const packageId = package_id || createGuidedPackageId(projectId, photos);
  requiredString(packageId, 'package_id');

  const seen = new Set(); const prepared = [];
  for (const photo of photos) {
    const photoId = requiredString(photo?.photo_id, 'photo_id');
    if (seen.has(photoId)) throw new Error(`photo_id dupliqué: ${photoId}`);
    seen.add(photoId);
    const originalFilename = requiredString(photo.original_filename, `original_filename pour ${photoId}`);
    if (!(photo.blob instanceof Blob) || photo.blob.size <= 0) throw new Error(`blob absent ou vide pour ${photoId}`);
    const orientation = optionalString(photo.orientation) ?? optionalString(photo.primary_face);
    const description = optionalString(photo.description) ?? optionalString(photo.note);
    const provenance = description !== null ? 'USER_CONFIRMED' : null;
    const filePath = `photos/${photoId}${extension(originalFilename)}`;
    prepared.push({ photo_id: photoId, orientation, description, must_reproduce: [], do_not_confuse: [], known_dimensions: [], connections_to_other_photos: [], provenance, original_filename: originalFilename, file_path: filePath, bytes: new Uint8Array(await photo.blob.arrayBuffer()) });
  }

  const guided = {
    schema_version: GUIDED_HOUSE_SCHEMA_VERSION,
    project_id: projectId,
    package_id: packageId,
    known_front_width: project.known_front_width ?? null,
    general_notes: typeof project.general_notes === 'string' ? project.general_notes : '',
    photos: prepared.map(({ bytes, ...photo }) => photo),
  };
  const manifest = {
    schema_version: GUIDED_HOUSE_SCHEMA_VERSION,
    project_id: projectId,
    package_id: packageId,
    guided_data_path: 'guided-house.json',
    photos: prepared.map(photo => ({ photo_id: photo.photo_id, file_path: photo.file_path, original_filename: photo.original_filename })),
  };
  const entries = [
    { name: 'manifest.json', bytes: encoder.encode(`${JSON.stringify(manifest, null, 2)}\n`) },
    { name: 'guided-house.json', bytes: encoder.encode(`${JSON.stringify(guided, null, 2)}\n`) },
    ...prepared.map(photo => ({ name: photo.file_path, bytes: photo.bytes })),
  ];
  return { filename: `BOLDUNGO_GUIDED_${projectId}_V1.zip`, manifest, guided, blob: new Blob([zip(entries)], { type: 'application/zip' }) };
}

export async function buildActiveGuidedHousePackageV1(options) {
  return buildGuidedHousePackageV1(await getActiveProjectSnapshot(), options);
}
