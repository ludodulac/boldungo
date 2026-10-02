import {
  getActiveProjectSnapshot,
  PRIMARY_FACES,
} from './project-photo-store.js';


function requireNonEmptyString(value, label) {
  if (typeof value !== 'string' || !value.trim()) {
    throw new Error(`${label} requis`);
  }
  return value;
}


export function normalizeActiveProjectSnapshotForPackageV1(snapshot) {
  const project = snapshot?.project ?? null;
  const photos = Array.isArray(snapshot?.photos) ? snapshot.photos : [];

  if (!project) {
    throw new Error('Aucun projet actif');
  }

  const projectId = requireNonEmptyString(project.project_id, 'project_id');

  if (!photos.length) {
    throw new Error('Aucune photo active');
  }

  const seenPhotoIds = new Set();
  const normalizedPhotos = photos.map((photo) => {
    const photoId = requireNonEmptyString(photo?.photo_id, 'photo_id');
    if (seenPhotoIds.has(photoId)) {
      throw new Error(`photo_id dupliqué: ${photoId}`);
    }
    seenPhotoIds.add(photoId);

    const primaryFace = photo?.primary_face;
    if (!PRIMARY_FACES.includes(primaryFace)) {
      throw new Error(
        `primary_face manquant ou invalide pour ${photoId}: ${String(primaryFace)}`,
      );
    }

    const originalFilename = requireNonEmptyString(
      photo?.original_filename,
      `original_filename pour ${photoId}`,
    );

    const blob = photo?.blob;
    if (!(blob instanceof Blob) || blob.size <= 0) {
      throw new Error(`blob absent ou vide pour ${photoId}`);
    }

    const note = photo?.note ?? null;
    if (note !== null && typeof note !== 'string') {
      throw new Error(`note invalide pour ${photoId}`);
    }

    return {
      photo_id: photoId,
      primary_face: primaryFace,
      original_filename: originalFilename,
      blob,
      note,
    };
  });

  return {
    project_id: projectId,
    photos: normalizedPhotos,
  };
}


export async function getActiveProjectPackageInputV1() {
  const snapshot = await getActiveProjectSnapshot();
  return normalizeActiveProjectSnapshotForPackageV1(snapshot);
}
