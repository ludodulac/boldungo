const MANIFEST_SCHEMA_VERSION = 'boldungo.analysis-package-manifest.v1';
const PRIMARY_FACES = new Set(['FRONT', 'RIGHT', 'LEFT', 'REAR']);
const TECHNICAL_ID_RE = /^[A-Za-z0-9][A-Za-z0-9_-]*$/;
const ROUND_ID_RE = /^R\d{3,}$/;
const PHOTO_ID_RE = /^(FRONT|RIGHT|LEFT|REAR)_\d{3,}$/;
const PACKAGE_ID_RE = /^PKG_[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;
const EXTENSION_RE = /\.[A-Za-z0-9]+$/;

const encoder = new TextEncoder();


function requireNonEmptyString(value, label) {
  if (typeof value !== 'string' || !value.trim()) {
    throw new Error(`${label} requis`);
  }
  return value;
}


function requireTechnicalId(value, label) {
  const candidate = requireNonEmptyString(value, label);
  if (!TECHNICAL_ID_RE.test(candidate)) {
    throw new Error(`${label} invalide`);
  }
  return candidate;
}


function originalExtension(filename) {
  const candidate = requireNonEmptyString(filename, 'original_filename');
  const match = candidate.match(EXTENSION_RE);
  if (!match) {
    throw new Error(`extension originale impossible à déterminer: ${candidate}`);
  }
  return match[0];
}


function requirePackageId(value) {
  if (typeof value !== 'string' || !PACKAGE_ID_RE.test(value)) {
    throw new Error('package_id invalide');
  }
  return value;
}


function dosDateTime() {
  return { date: 0x0021, time: 0x0000 };
}


function makeCrc32Table() {
  const table = new Uint32Array(256);
  for (let n = 0; n < 256; n += 1) {
    let c = n;
    for (let k = 0; k < 8; k += 1) {
      c = (c & 1) ? (0xedb88320 ^ (c >>> 1)) : (c >>> 1);
    }
    table[n] = c >>> 0;
  }
  return table;
}


const CRC32_TABLE = makeCrc32Table();


function crc32(bytes) {
  let crc = 0xffffffff;
  for (const byte of bytes) {
    crc = CRC32_TABLE[(crc ^ byte) & 0xff] ^ (crc >>> 8);
  }
  return (crc ^ 0xffffffff) >>> 0;
}


function concatBytes(chunks) {
  const total = chunks.reduce((sum, chunk) => sum + chunk.length, 0);
  const result = new Uint8Array(total);
  let offset = 0;
  for (const chunk of chunks) {
    result.set(chunk, offset);
    offset += chunk.length;
  }
  return result;
}


function u16(value) {
  const bytes = new Uint8Array(2);
  new DataView(bytes.buffer).setUint16(0, value, true);
  return bytes;
}


function u32(value) {
  const bytes = new Uint8Array(4);
  new DataView(bytes.buffer).setUint32(0, value >>> 0, true);
  return bytes;
}


function localFileHeader(nameBytes, dataBytes, crc) {
  const { date, time } = dosDateTime();
  return concatBytes([
    u32(0x04034b50),
    u16(20),
    u16(0x0800),
    u16(0),
    u16(time),
    u16(date),
    u32(crc),
    u32(dataBytes.length),
    u32(dataBytes.length),
    u16(nameBytes.length),
    u16(0),
    nameBytes,
  ]);
}


function centralDirectoryHeader(nameBytes, dataBytes, crc, localOffset) {
  const { date, time } = dosDateTime();
  return concatBytes([
    u32(0x02014b50),
    u16(20),
    u16(20),
    u16(0x0800),
    u16(0),
    u16(time),
    u16(date),
    u32(crc),
    u32(dataBytes.length),
    u32(dataBytes.length),
    u16(nameBytes.length),
    u16(0),
    u16(0),
    u16(0),
    u16(0),
    u32(0),
    u32(localOffset),
    nameBytes,
  ]);
}


function endOfCentralDirectory(entryCount, centralSize, centralOffset) {
  return concatBytes([
    u32(0x06054b50),
    u16(0),
    u16(0),
    u16(entryCount),
    u16(entryCount),
    u32(centralSize),
    u32(centralOffset),
    u16(0),
  ]);
}


function buildStoredZip(entries) {
  if (entries.length > 0xffff) {
    throw new Error('trop de fichiers pour ZIP V1');
  }

  const localChunks = [];
  const centralChunks = [];
  let localOffset = 0;

  for (const entry of entries) {
    const nameBytes = encoder.encode(entry.name);
    const dataBytes = entry.bytes;
    const crc = crc32(dataBytes);
    const header = localFileHeader(nameBytes, dataBytes, crc);
    localChunks.push(header, dataBytes);
    centralChunks.push(
      centralDirectoryHeader(nameBytes, dataBytes, crc, localOffset),
    );
    localOffset += header.length + dataBytes.length;
  }

  const centralDirectory = concatBytes(centralChunks);
  return concatBytes([
    ...localChunks,
    centralDirectory,
    endOfCentralDirectory(entries.length, centralDirectory.length, localOffset),
  ]);
}


function manifestCreatedAt() {
  return new Date().toISOString().replace(/\.\d{3}Z$/, 'Z');
}


async function normalizePackageInput(packageInput) {
  if (!packageInput || typeof packageInput !== 'object' || Array.isArray(packageInput)) {
    throw new Error('package_input invalide');
  }

  const projectId = requireTechnicalId(packageInput.project_id, 'project_id');
  if (!Array.isArray(packageInput.photos)) {
    throw new Error('package_input.photos invalide');
  }
  if (!packageInput.photos.length) {
    throw new Error('aucune photo');
  }

  const photoIds = new Set();
  const filePaths = new Set();
  const prepared = [];

  for (const photo of packageInput.photos) {
    if (!photo || typeof photo !== 'object' || Array.isArray(photo)) {
      throw new Error('photo invalide');
    }

    const photoId = requireNonEmptyString(photo.photo_id, 'photo_id');
    if (!PHOTO_ID_RE.test(photoId)) {
      throw new Error(`photo_id invalide: ${photoId}`);
    }
    if (photoIds.has(photoId)) {
      throw new Error(`photo_id dupliqué: ${photoId}`);
    }
    photoIds.add(photoId);

    const primaryFace = photo.primary_face;
    if (!PRIMARY_FACES.has(primaryFace)) {
      throw new Error(`primary_face invalide pour ${photoId}`);
    }
    if (!photoId.startsWith(`${primaryFace}_`)) {
      throw new Error(`photo_id ${photoId} incompatible avec primary_face ${primaryFace}`);
    }

    const originalFilename = requireNonEmptyString(
      photo.original_filename,
      `original_filename pour ${photoId}`,
    );
    const extension = originalExtension(originalFilename);
    const filePath = `photos/${photoId}${extension}`;
    if (filePaths.has(filePath)) {
      throw new Error(`file_path dupliqué: ${filePath}`);
    }
    filePaths.add(filePath);

    if (!(photo.blob instanceof Blob) || photo.blob.size <= 0) {
      throw new Error(`Blob absent ou vide pour ${photoId}`);
    }

    const note = photo.note ?? null;
    if (note !== null && typeof note !== 'string') {
      throw new Error(`note invalide pour ${photoId}`);
    }

    prepared.push({
      photo_id: photoId,
      primary_face: primaryFace,
      original_filename: originalFilename,
      file_path: filePath,
      note,
      bytes: new Uint8Array(await photo.blob.arrayBuffer()),
    });
  }

  return { projectId, prepared };
}


export async function buildAnalysisPackageZipV1({
  package_input,
  agent_id,
  agent_display_name,
  round_id,
  package_id,
  prompt_text,
}) {
  const { projectId, prepared } = await normalizePackageInput(package_input);
  const agentId = requireTechnicalId(agent_id, 'agent_id');
  const agentDisplayName = requireNonEmptyString(
    agent_display_name,
    'agent_display_name',
  );

  if (typeof round_id !== 'string' || !ROUND_ID_RE.test(round_id)) {
    throw new Error('round_id invalide');
  }
  requirePackageId(package_id);
  if (typeof prompt_text !== 'string') {
    throw new Error('prompt_text invalide');
  }

  const manifest = {
    schema_version: MANIFEST_SCHEMA_VERSION,
    project_id: projectId,
    agent_id: agentId,
    agent_display_name: agentDisplayName,
    round_id,
    package_id,
    created_at: manifestCreatedAt(),
    prompt_path: 'prompt.txt',
    photos: prepared.map(photo => ({
      photo_id: photo.photo_id,
      file_path: photo.file_path,
      primary_face: photo.primary_face,
      original_filename: photo.original_filename,
      note: photo.note,
    })),
  };

  const entries = [
    {
      name: 'manifest.json',
      bytes: encoder.encode(`${JSON.stringify(manifest, null, 2)}\n`),
    },
    {
      name: 'prompt.txt',
      bytes: encoder.encode(prompt_text),
    },
    ...prepared.map(photo => ({
      name: photo.file_path,
      bytes: photo.bytes,
    })),
  ];

  const zipBytes = buildStoredZip(entries);
  const filename = `BOLDUNGO_${projectId}_${agentId}_${round_id}.zip`;

  return {
    filename,
    blob: new Blob([zipBytes], { type: 'application/zip' }),
  };
}
