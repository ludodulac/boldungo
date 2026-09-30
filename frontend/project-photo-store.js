export const PROJECT_SCHEMA_VERSION = 1;
export const PRIMARY_FACES = ['FRONT', 'RIGHT', 'LEFT', 'REAR'];
export const DETAIL_GROUP_IDS = ['detail_1', 'detail_2', 'detail_3', 'detail_4', 'detail_5', 'detail_6'];
export const MAX_PHOTOS_PER_GROUP = 4;

const DB_NAME = 'boldungo-project-photo-intake';
const DB_VERSION = 2;
const STORE_PROJECTS = 'projects';
const LEGACY_STORE_PHOTOS = 'photos';
const STORE_PHOTOS = 'photos_v2';
const STORE_SETTINGS = 'settings';
const ACTIVE_PROJECT_KEY = 'active_project_id';

const FACE_PREFIX = {
  FRONT: 'FRONT',
  RIGHT: 'RIGHT',
  LEFT: 'LEFT',
  REAR: 'REAR',
};

function requestResult(request) {
  return new Promise((resolve, reject) => {
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error || new Error('IndexedDB request failed'));
  });
}

function transactionDone(transaction) {
  return new Promise((resolve, reject) => {
    transaction.oncomplete = () => resolve();
    transaction.onabort = () => reject(transaction.error || new Error('IndexedDB transaction aborted'));
    transaction.onerror = () => reject(transaction.error || new Error('IndexedDB transaction failed'));
  });
}

function nowIso() {
  return new Date().toISOString();
}

function randomId() {
  if (globalThis.crypto?.randomUUID) return globalThis.crypto.randomUUID();
  return `\${Date.now().toString(36)}-\${Math.random().toString(36).slice(2)}`;
}

function defaultGroupNotes() {
  return {
    front: '',
    right: '',
    left: '',
    rear: '',
    detail_1: '',
    detail_2: '',
    detail_3: '',
    detail_4: '',
    detail_5: '',
    detail_6: '',
  };
}

function defaultCounters() {
  return { FRONT: 0, RIGHT: 0, LEFT: 0, REAR: 0, DETAIL: 0 };
}

export function createProjectRecord(projectName) {
  const normalizedName = String(projectName || '').trim();
  if (!normalizedName) throw new Error('Nom du projet requis');
  const timestamp = nowIso();
  return {
    schema_version: PROJECT_SCHEMA_VERSION,
    project_id: `project_\${randomId()}`,
    project_name: normalizedName,
    city: '',
    known_front_width: null,
    general_notes: '',
    model_size: '48',
    created_at: timestamp,
    updated_at: timestamp,
    photo_id_counters: defaultCounters(),
    group_notes: defaultGroupNotes(),
    detail_groups: DETAIL_GROUP_IDS.map((detail_group_id, index) => ({
      detail_group_id,
      label: `Détail \${index + 1}`,
    })),
    orientation_confirmed: false,
    name_confirmed: true,
    clarifications: [],
    human_facts: [],
  };
}

export function canonicalFaceForSlot(slotName) {
  const upper = String(slotName || '').toUpperCase();
  return PRIMARY_FACES.includes(upper) ? upper : null;
}

export function photoGroupKey(photo) {
  if (photo.primary_face) return String(photo.primary_face).toLowerCase();
  return photo.detail_group_id || null;
}

export function photoRecordToFile(photo) {
  const blob = photo.blob instanceof Blob
    ? photo.blob
    : new Blob([photo.blob], { type: photo.mime_type || 'application/octet-stream' });
  return new File([blob], photo.original_filename || photo.photo_id, {
    type: photo.mime_type || blob.type || 'application/octet-stream',
    lastModified: Date.parse(photo.created_at || '') || Date.now(),
  });
}

export async function openProjectDb() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onupgradeneeded = () => {
      const database = request.result;
      if (!database.objectStoreNames.contains(STORE_PROJECTS)) {
        database.createObjectStore(STORE_PROJECTS, { keyPath: 'project_id' });
      }
      if (!database.objectStoreNames.contains(STORE_PHOTOS)) {
        const photos = database.createObjectStore(STORE_PHOTOS, { keyPath: ['project_id', 'photo_id'] });
        photos.createIndex('project_id', 'project_id', { unique: false });

        // 080B migration: retain v1 photos while moving to a composite key so
        // FRONT_001 can exist independently in several projects.
        if (database.objectStoreNames.contains(LEGACY_STORE_PHOTOS)) {
          const legacy = request.transaction.objectStore(LEGACY_STORE_PHOTOS);
          const cursorRequest = legacy.openCursor();
          cursorRequest.onsuccess = () => {
            const cursor = cursorRequest.result;
            if (!cursor) return;
            photos.put(cursor.value);
            cursor.continue();
          };
        }
      }
      if (!database.objectStoreNames.contains(STORE_SETTINGS)) {
        database.createObjectStore(STORE_SETTINGS, { keyPath: 'key' });
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error || new Error('IndexedDB unavailable'));
  });
}

export async function listProjects() {
  const database = await openProjectDb();
  const tx = database.transaction(STORE_PROJECTS, 'readonly');
  const projects = await requestResult(tx.objectStore(STORE_PROJECTS).getAll());
  await transactionDone(tx);
  return projects.sort((a, b) => String(b.updated_at).localeCompare(String(a.updated_at)));
}

export async function setActiveProjectId(projectId) {
  const database = await openProjectDb();
  const tx = database.transaction(STORE_SETTINGS, 'readwrite');
  tx.objectStore(STORE_SETTINGS).put({ key: ACTIVE_PROJECT_KEY, value: projectId });
  await transactionDone(tx);
}

export async function createProject(projectName) {
  const database = await openProjectDb();
  const project = createProjectRecord(projectName);
  const tx = database.transaction([STORE_PROJECTS, STORE_SETTINGS], 'readwrite');
  tx.objectStore(STORE_PROJECTS).put(project);
  tx.objectStore(STORE_SETTINGS).put({ key: ACTIVE_PROJECT_KEY, value: project.project_id });
  await transactionDone(tx);
  return project;
}

export async function getProject(projectId) {
  if (!projectId) return null;
  const database = await openProjectDb();
  const tx = database.transaction(STORE_PROJECTS, 'readonly');
  const project = await requestResult(tx.objectStore(STORE_PROJECTS).get(projectId));
  await transactionDone(tx);
  return project || null;
}

export async function getActiveProject() {
  const database = await openProjectDb();
  const tx = database.transaction([STORE_SETTINGS, STORE_PROJECTS], 'readonly');
  const settingsStore = tx.objectStore(STORE_SETTINGS);
  const projectsStore = tx.objectStore(STORE_PROJECTS);
  const activeSetting = await requestResult(settingsStore.get(ACTIVE_PROJECT_KEY));
  const activeProject = activeSetting?.value
    ? await requestResult(projectsStore.get(activeSetting.value))
    : null;
  await transactionDone(tx);
  if (activeProject) return activeProject;

  const projects = await listProjects();
  if (projects.length) {
    await setActiveProjectId(projects[0].project_id);
    return projects[0];
  }
  return null;
}

export async function updateProject(projectId, patch) {
  const database = await openProjectDb();
  const tx = database.transaction(STORE_PROJECTS, 'readwrite');
  const store = tx.objectStore(STORE_PROJECTS);
  const existing = await requestResult(store.get(projectId));
  if (!existing) {
    tx.abort();
    throw new Error('Projet introuvable');
  }
  const updated = {
    ...existing,
    ...patch,
    schema_version: PROJECT_SCHEMA_VERSION,
    project_id: existing.project_id,
    created_at: existing.created_at,
    updated_at: nowIso(),
  };
  store.put(updated);
  await transactionDone(tx);
  return updated;
}

export async function getProjectPhotos(projectId) {
  const database = await openProjectDb();
  const tx = database.transaction(STORE_PHOTOS, 'readonly');
  const photos = await requestResult(tx.objectStore(STORE_PHOTOS).index('project_id').getAll(projectId));
  await transactionDone(tx);
  return photos.sort((a, b) => {
    const groupCompare = String(photoGroupKey(a)).localeCompare(String(photoGroupKey(b)));
    return groupCompare || Number(a.capture_order) - Number(b.capture_order);
  });
}

function matchesGroup(photo, primaryFace, detailGroupId) {
  if (primaryFace) return photo.primary_face === primaryFace;
  return photo.detail_group_id === detailGroupId;
}

export async function addPhotosToProject(projectId, {
  primaryFace = null,
  detailGroupId = null,
  files = [],
  note = '',
} = {}) {
  const normalizedFace = primaryFace ? String(primaryFace).toUpperCase() : null;
  if (normalizedFace && !PRIMARY_FACES.includes(normalizedFace)) throw new Error('PRIMARY_FACE invalide');
  if (!normalizedFace && !DETAIL_GROUP_IDS.includes(detailGroupId)) throw new Error('detail_group_id invalide');

  const database = await openProjectDb();
  const tx = database.transaction([STORE_PROJECTS, STORE_PHOTOS], 'readwrite');
  const projectStore = tx.objectStore(STORE_PROJECTS);
  const photoStore = tx.objectStore(STORE_PHOTOS);
  const projectRequest = projectStore.get(projectId);
  const photosRequest = photoStore.index('project_id').getAll(projectId);
  const [project, existingPhotos] = await Promise.all([
    requestResult(projectRequest),
    requestResult(photosRequest),
  ]);
  if (!project) {
    tx.abort();
    throw new Error('Projet introuvable');
  }

  const inGroup = existingPhotos.filter(photo => matchesGroup(photo, normalizedFace, detailGroupId));
  const available = Math.max(0, MAX_PHOTOS_PER_GROUP - inGroup.length);
  const acceptedFiles = [...files].slice(0, available);
  const counters = { ...defaultCounters(), ...(project.photo_id_counters || {}) };
  const counterKey = normalizedFace || 'DETAIL';
  let captureOrder = inGroup.reduce((max, photo) => Math.max(max, Number(photo.capture_order) || 0), 0);
  const timestamp = nowIso();
  const added = [];

  for (const file of acceptedFiles) {
    counters[counterKey] += 1;
    captureOrder += 1;
    const prefix = normalizedFace ? FACE_PREFIX[normalizedFace] : 'DETAIL';
    const photoId = `\${prefix}_\${String(counters[counterKey]).padStart(3, '0')}`;
    const record = {
      project_id: projectId,
      photo_id: photoId,
      primary_face: normalizedFace,
      detail_group_id: normalizedFace ? null : detailGroupId,
      original_filename: file.name || photoId,
      mime_type: file.type || 'application/octet-stream',
      blob: file,
      capture_order: captureOrder,
      note: String(note || ''),
      created_at: timestamp,
    };
    photoStore.put(record);
    added.push(record);
  }

  projectStore.put({
    ...project,
    photo_id_counters: counters,
    updated_at: timestamp,
  });
  await transactionDone(tx);
  return {
    added,
    rejected_count: Math.max(0, files.length - acceptedFiles.length),
    group_count: inGroup.length + added.length,
  };
}

export async function deleteProjectPhoto(projectId, photoId) {
  const database = await openProjectDb();
  const tx = database.transaction([STORE_PROJECTS, STORE_PHOTOS], 'readwrite');
  const projectStore = tx.objectStore(STORE_PROJECTS);
  const photoStore = tx.objectStore(STORE_PHOTOS);
  const project = await requestResult(projectStore.get(projectId));
  if (!project) {
    tx.abort();
    throw new Error('Projet introuvable');
  }
  photoStore.delete([projectId, photoId]);
  projectStore.put({ ...project, updated_at: nowIso() });
  await transactionDone(tx);
}

export async function updateGroupNote(projectId, groupKey, note) {
  const database = await openProjectDb();
  const tx = database.transaction([STORE_PROJECTS, STORE_PHOTOS], 'readwrite');
  const projectStore = tx.objectStore(STORE_PROJECTS);
  const photoStore = tx.objectStore(STORE_PHOTOS);
  const projectRequest = projectStore.get(projectId);
  const photosRequest = photoStore.index('project_id').getAll(projectId);
  const [project, photos] = await Promise.all([
    requestResult(projectRequest),
    requestResult(photosRequest),
  ]);
  if (!project) {
    tx.abort();
    throw new Error('Projet introuvable');
  }

  const groupNotes = { ...defaultGroupNotes(), ...(project.group_notes || {}), [groupKey]: String(note || '') };
  projectStore.put({ ...project, group_notes: groupNotes, updated_at: nowIso() });
  for (const photo of photos) {
    if (photoGroupKey(photo) === groupKey) photoStore.put({ ...photo, note: String(note || '') });
  }
  await transactionDone(tx);
}

export async function getActiveProjectSnapshot() {
  const project = await getActiveProject();
  if (!project) return { project: null, photos: [] };
  const photos = await getProjectPhotos(project.project_id);
  return { project, photos };
}
