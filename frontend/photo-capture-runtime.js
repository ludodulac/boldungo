import {
  MAX_PHOTOS_PER_GROUP,
  addPhotosToProject,
  canonicalFaceForSlot,
  createProject,
  deleteProjectPhoto,
  getActiveProjectSnapshot,
  listProjects,
  setActiveProjectId,
  updateGroupNote,
  updateProject,
} from './project-photo-store.js';

const packageStatus = document.querySelector('#ai-package-status');
const technicalPhotos = document.querySelector('#photos');
const baseSlots = [...document.querySelectorAll('.guided-photo-slot')];
const detailSlots = [...document.querySelectorAll('.detail-photo-slot')];
const saveStatus = document.querySelector('#project-save-status');
const projectPicker = document.querySelector('#project-picker');
const newProjectButton = document.querySelector('#new-project');
const projectName = document.querySelector('#project-name');
const city = document.querySelector('#city');
const knownWidth = document.querySelector('#known-width');
const notes = document.querySelector('#notes');
const studs = document.querySelector('#studs');

const previewUrls = new Map();
const debounceTimers = new Map();
let activeProject = null;
let activePhotos = [];
let saveQueue = Promise.resolve();
window.boldungoProjectPhotoSavePromise = saveQueue;

function setSaveStatus(message, kind = 'ok') {
  if (!saveStatus) return;
  saveStatus.textContent = message;
  saveStatus.dataset.kind = kind;
}

function queueSave(task) {
  setSaveStatus('Enregistrement…', 'pending');
  const operation = saveQueue.then(task);
  saveQueue = operation.catch(() => undefined);
  window.boldungoProjectPhotoSavePromise = operation;
  operation.then(
    () => setSaveStatus('Enregistré sur cet appareil', 'ok'),
    error => {
      console.error(error);
      setSaveStatus('Erreur de sauvegarde', 'error');
    },
  );
  return operation;
}

function debounceSave(key, task, delay = 250) {
  window.clearTimeout(debounceTimers.get(key));
  debounceTimers.set(key, window.setTimeout(() => queueSave(task), delay));
}

function ensureOrientationControl() {
  let control = document.querySelector('#orientation-confirmation-field');
  if (control) return control;
  const grid = document.querySelector('#guided-photo-grid');
  if (!grid) return null;
  control = document.createElement('div');
  control.id = 'orientation-confirmation-field';
  control.className = 'field orientation-confirmation-field';
  control.innerHTML = \`
    <label class="orientation-confirmation-label">
      <input id="confirm-guided-orientations" type="checkbox" />
      <span><strong>J’ai vérifié le classement principal de mes vues</strong><br><small>Une vue trois-quarts reste classée une seule fois selon sa face principale. Elle peut montrer d’autres faces sans être dupliquée.</small></span>
    </label>\`;
  grid.insertAdjacentElement('afterend', control);
  return control;
}

function filesForSlot(slot, inputSelector) {
  return [...(slot.querySelector(inputSelector)?.files ?? [])].slice(0, MAX_PHOTOS_PER_GROUP);
}

function selectedFiles() {
  return [
    ...baseSlots.flatMap(slot => filesForSlot(slot, '.guided-photo-input')),
    ...detailSlots.flatMap(slot => filesForSlot(slot, '.detail-photo-input')),
  ];
}

function syncTechnicalPhotoInput() {
  if (!technicalPhotos || typeof DataTransfer === 'undefined') return;
  const transfer = new DataTransfer();
  for (const file of selectedFiles()) transfer.items.add(file);
  technicalPhotos.files = transfer.files;
  technicalPhotos.dispatchEvent(new Event('change', { bubbles: true }));
}

function clearPreviewUrls(slotKey) {
  for (const url of previewUrls.get(slotKey) || []) URL.revokeObjectURL(url);
  previewUrls.set(slotKey, []);
}

function ensurePersistedList(slot, input) {
  let list = slot.querySelector(':scope > .persisted-photo-list');
  if (list) return list;
  list = document.createElement('div');
  list.className = 'persisted-photo-list';
  list.setAttribute('aria-live', 'polite');
  input.insertAdjacentElement('afterend', list);
  return list;
}

function groupKeyForSlot(slot) {
  return slot.dataset.slot;
}

function photosForSlot(slot) {
  const key = groupKeyForSlot(slot);
  const face = canonicalFaceForSlot(key);
  return activePhotos
    .filter(photo => face ? photo.primary_face === face : photo.detail_group_id === key)
    .sort((a, b) => Number(a.capture_order) - Number(b.capture_order));
}

function renderPersistedSlot(slot, inputSelector, nameSelector) {
  const input = slot.querySelector(inputSelector);
  const name = slot.querySelector(nameSelector);
  if (!input) return;
  const key = groupKeyForSlot(slot);
  const records = photosForSlot(slot);
  const list = ensurePersistedList(slot, input);
  clearPreviewUrls(key);
  list.replaceChildren();
  list.dataset.count = String(records.length);
  slot.classList.toggle('has-photo', records.length > 0);
  slot.classList.toggle('has-persisted-photos', records.length > 0);

  const urls = [];
  for (const photo of records) {
    const item = document.createElement('article');
    item.className = 'persisted-photo-item';
    item.dataset.photoId = photo.photo_id;

    const image = document.createElement('img');
    image.className = 'persisted-photo-preview';
    image.alt = \`\${photo.photo_id} — \${photo.original_filename}\`;
    const url = URL.createObjectURL(photo.blob);
    urls.push(url);
    image.src = url;

    const meta = document.createElement('div');
    meta.className = 'persisted-photo-meta';
    const identity = document.createElement('strong');
    identity.textContent = photo.photo_id;
    const filename = document.createElement('small');
    filename.textContent = photo.original_filename;
    meta.append(identity, filename);

    const remove = document.createElement('button');
    remove.type = 'button';
    remove.className = 'persisted-photo-remove';
    remove.dataset.deletePhotoId = photo.photo_id;
    remove.textContent = 'Retirer';
    remove.setAttribute('aria-label', \`Retirer \${photo.photo_id}\`);

    item.append(image, meta, remove);
    list.appendChild(item);
  }
  previewUrls.set(key, urls);

  if (name) {
    if (!records.length) name.textContent = 'Aucune photo enregistrée';
    else if (records.length === 1) name.textContent = \`\${records[0].photo_id} enregistrée\`;
    else name.textContent = \`\${records.length} photos enregistrées\`;
  }
}

function populateFields(project) {
  if (projectName) projectName.value = project.project_name || '';
  if (city) city.value = project.city || '';
  if (knownWidth) knownWidth.value = project.known_front_width ?? '';
  if (notes) notes.value = project.general_notes || '';
  if (studs) studs.value = String(project.model_size || '48');

  const groupNotes = project.group_notes || {};
  for (const slot of [...baseSlots, ...detailSlots]) {
    const note = slot.querySelector('.guided-photo-note, .detail-photo-note');
    if (note) note.value = groupNotes[groupKeyForSlot(slot)] || '';
  }
  const confirmed = document.querySelector('#confirm-guided-orientations');
  if (confirmed) confirmed.checked = Boolean(project.orientation_confirmed);
}

async function refreshProjectPicker() {
  if (!projectPicker || !activeProject) return;
  const projects = await listProjects();
  projectPicker.replaceChildren();
  for (const project of projects) {
    const option = document.createElement('option');
    option.value = project.project_id;
    option.textContent = project.project_name || 'Projet sans nom';
    projectPicker.appendChild(option);
  }
  projectPicker.value = activeProject.project_id;
}

function renderAllSlots() {
  baseSlots.forEach(slot => renderPersistedSlot(slot, '.guided-photo-input', '.guided-photo-name'));
  detailSlots.forEach(slot => renderPersistedSlot(slot, '.detail-photo-input', '.detail-photo-name'));
}

async function reloadActiveProject() {
  const snapshot = await getActiveProjectSnapshot();
  activeProject = snapshot.project;
  activePhotos = snapshot.photos;
  populateFields(activeProject);
  await refreshProjectPicker();
  renderAllSlots();
  document.documentElement.dataset.projectPhotoIntakeReady = 'true';
  window.dispatchEvent(new CustomEvent('boldungo:project-photo-intake-ready', {
    detail: { project_id: activeProject.project_id },
  }));
  setSaveStatus('Enregistré sur cet appareil', 'ok');
}

async function addFilesFromSlot(slot, inputSelector) {
  if (!activeProject) return;
  const input = slot.querySelector(inputSelector);
  const files = [...(input?.files || [])];
  if (!files.length) return;
  const key = groupKeyForSlot(slot);
  const face = canonicalFaceForSlot(key);
  const note = slot.querySelector('.guided-photo-note, .detail-photo-note')?.value || '';

  const result = await addPhotosToProject(activeProject.project_id, {
    primaryFace: face,
    detailGroupId: face ? null : key,
    files,
    note,
  });
  if (result.rejected_count && packageStatus) {
    packageStatus.textContent = \`Maximum \${MAX_PHOTOS_PER_GROUP} photos par orientation/groupe. \${result.rejected_count} photo(s) non ajoutée(s).\`;
  }
  await reloadActiveProject();
}

function bindPhotoSlot(slot, inputSelector) {
  const input = slot.querySelector(inputSelector);
  input?.addEventListener('change', () => {
    syncTechnicalPhotoInput();
    queueSave(() => addFilesFromSlot(slot, inputSelector));
  });

  const note = slot.querySelector('.guided-photo-note, .detail-photo-note');
  note?.addEventListener('input', () => {
    const key = groupKeyForSlot(slot);
    debounceSave(\`note:\${key}\`, async () => {
      if (!activeProject) return;
      await updateGroupNote(activeProject.project_id, key, note.value);
      const snapshot = await getActiveProjectSnapshot();
      activeProject = snapshot.project;
      activePhotos = snapshot.photos;
    });
  });
}

function bindProjectField(element, field, normalize = value => value) {
  element?.addEventListener('input', () => {
    debounceSave(\`project:\${field}\`, async () => {
      if (!activeProject) return;
      activeProject = await updateProject(activeProject.project_id, {
        [field]: normalize(element.value),
      });
      if (field === 'project_name') await refreshProjectPicker();
    });
  });
}

function bindProjectControls() {
  bindProjectField(projectName, 'project_name', value => String(value || '').trim() || 'Ma maison');
  bindProjectField(city, 'city', value => String(value || '').trim());
  bindProjectField(knownWidth, 'known_front_width', value => {
    const number = Number(value);
    return Number.isFinite(number) && number > 0 ? number : null;
  });
  bindProjectField(notes, 'general_notes', value => String(value || ''));
  studs?.addEventListener('change', () => queueSave(async () => {
    if (!activeProject) return;
    activeProject = await updateProject(activeProject.project_id, { model_size: String(studs.value || '48') });
  }));

  const confirmed = document.querySelector('#confirm-guided-orientations');
  confirmed?.addEventListener('change', () => queueSave(async () => {
    if (!activeProject) return;
    activeProject = await updateProject(activeProject.project_id, { orientation_confirmed: confirmed.checked });
  }));

  projectPicker?.addEventListener('change', () => queueSave(async () => {
    await setActiveProjectId(projectPicker.value);
    await reloadActiveProject();
  }));

  newProjectButton?.addEventListener('click', () => queueSave(async () => {
    activeProject = await createProject('Ma maison');
    activePhotos = [];
    await reloadActiveProject();
    projectName?.focus();
    projectName?.select();
  }));
}

document.addEventListener('click', event => {
  const button = event.target?.closest?.('[data-delete-photo-id]');
  if (!button || !activeProject) return;
  const photoId = button.dataset.deletePhotoId;
  queueSave(async () => {
    await deleteProjectPhoto(activeProject.project_id, photoId);
    await reloadActiveProject();
  });
});

async function init() {
  ensureOrientationControl();
  baseSlots.forEach(slot => bindPhotoSlot(slot, '.guided-photo-input'));
  detailSlots.forEach(slot => bindPhotoSlot(slot, '.detail-photo-input'));
  bindProjectControls();
  syncTechnicalPhotoInput();
  try {
    await reloadActiveProject();
  } catch (error) {
    console.error(error);
    setSaveStatus('Erreur de sauvegarde', 'error');
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init, { once: true });
} else {
  init();
}
