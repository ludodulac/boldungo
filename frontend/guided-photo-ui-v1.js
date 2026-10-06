import { getActiveProjectSnapshot, updateProjectPhotoGuidance } from './project-photo-store.js';
import { buildActiveGuidedHousePackageV1 } from './guided-house-package-v1.js';

const fields = [
  ['description', 'Description', 'Cette photo montre…'],
  ['must_reproduce', 'À reproduire absolument', 'escalier, porte, terrasse, poteaux'],
  ['do_not_confuse', 'À ne pas confondre', 'La construction visible à gauche appartient au voisin'],
  ['known_dimensions', 'Dimensions connues', 'largeur porte = 90 cm'],
  ['connections_to_other_photos', 'Liens avec d’autres photos', 'même terrasse que photo 4, vue depuis l’autre côté'],
];
const orientations = ['FRONT','RIGHT','LEFT','REAR','DETAIL','UNKNOWN'];
const host = document.querySelector('#guided-photo-editor');
const exportButton = document.querySelector('#export-guided-package');
const status = document.querySelector('#guided-export-status');
let saveTimer = null;

function text(value) { return typeof value === 'string' ? value : ''; }
function listText(value) { return Array.isArray(value) ? value.join('\n') : text(value); }
function escapeHtml(value) { return String(value).replace(/[&<>\"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;'}[c])); }
function download(blob, filename) {
  const url = URL.createObjectURL(blob); const a = document.createElement('a');
  a.href = url; a.download = filename; document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
}

function card(photo) {
  const orientation = photo.orientation || photo.primary_face || (photo.detail_group_id ? 'DETAIL' : 'UNKNOWN');
  return `<article class="guided-editor-card" data-photo-id="${escapeHtml(photo.photo_id)}">
    <div class="guided-editor-head"><img data-preview-photo="${escapeHtml(photo.photo_id)}" alt="${escapeHtml(photo.original_filename)}"><div><strong>${escapeHtml(photo.photo_id)}</strong><small>${escapeHtml(photo.original_filename)}</small></div></div>
    <label>Orientation<select data-guided-field="orientation">${orientations.map(v => `<option value="${v}"${v===orientation?' selected':''}>${v}</option>`).join('')}</select></label>
    ${fields.map(([key,label,placeholder]) => `<label>${label}<textarea rows="2" data-guided-field="${key}" placeholder="${escapeHtml(placeholder)}">${escapeHtml(key === 'description' ? (photo.description ?? photo.note ?? '') : listText(photo[key]))}</textarea></label>`).join('')}
  </article>`;
}

async function render() {
  if (!host) return;
  const snapshot = await getActiveProjectSnapshot();
  host.innerHTML = snapshot.photos.length ? snapshot.photos.map(card).join('') : '<p class="microcopy">Ajoutez une photo ci-dessus pour renseigner ses informations.</p>';
  for (const photo of snapshot.photos) {
    const img = host.querySelector(`[data-preview-photo="${CSS.escape(photo.photo_id)}"]`);
    if (img) img.src = URL.createObjectURL(photo.blob);
  }
}

host?.addEventListener('input', event => {
  const field = event.target.dataset.guidedField;
  if (!field) return;
  const cardEl = event.target.closest('[data-photo-id]');
  clearTimeout(saveTimer);
  saveTimer = setTimeout(async () => {
    const raw = event.target.value;
    const value = ['must_reproduce','do_not_confuse','known_dimensions','connections_to_other_photos'].includes(field)
      ? raw.split(/\n|,/).map(v => v.trim()).filter(Boolean)
      : raw;
    await updateProjectPhotoGuidance(cardEl.dataset.photoId, { [field]: value, provenance: 'USER_CONFIRMED' });
  }, 250);
});
host?.addEventListener('change', event => event.target.dispatchEvent(new Event('input', { bubbles:true })));

exportButton?.addEventListener('click', async () => {
  try {
    status.textContent = 'Préparation du dossier…';
    await window.boldungoProjectPhotoSavePromise;
    const built = await buildActiveGuidedHousePackageV1();
    download(built.blob, built.filename);
    status.textContent = 'Dossier guidé exporté.';
  } catch (error) { status.textContent = `Export impossible : ${error.message}`; }
});

window.addEventListener('boldungo:project-photo-intake-ready', render);
render();
