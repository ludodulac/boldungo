import { getActiveProjectPackageInputV1 } from './analysis-package-input-v1.js';
import { buildAnalysisPackageZipV1 } from './analysis-package-zip-v1.js';
import { INITIAL_SOPHIE_PROMPT_V1 } from './analysis-prompt-v1-initial.js';
import { appendAnalysisPackageExport } from './project-photo-store.js';


export const SOPHIE_AGENT_ID = 'SOPHIE';
export const SOPHIE_AGENT_DISPLAY_NAME = 'Sophie';
export const SOPHIE_INITIAL_ROUND_ID = 'R001';


export function createPackageIdV1() {
  if (!globalThis.crypto?.randomUUID) {
    throw new Error('crypto.randomUUID indisponible');
  }
  return `PKG_${globalThis.crypto.randomUUID()}`;
}


export function downloadPackageBlob(blob, filename) {
  if (!(blob instanceof Blob) || blob.size <= 0) {
    throw new Error('Blob ZIP invalide');
  }
  if (typeof filename !== 'string' || !filename.trim()) {
    throw new Error('Nom ZIP invalide');
  }
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}


export async function downloadInitialSophiePackageV1({
  getPackageInput = getActiveProjectPackageInputV1,
  buildPackage = buildAnalysisPackageZipV1,
  persistExport = appendAnalysisPackageExport,
  packageIdFactory = createPackageIdV1,
  download = downloadPackageBlob,
  now = () => new Date().toISOString(),
} = {}) {
  const packageInput = await getPackageInput();
  const packageId = packageIdFactory();

  const built = await buildPackage({
    package_input: packageInput,
    agent_id: SOPHIE_AGENT_ID,
    agent_display_name: SOPHIE_AGENT_DISPLAY_NAME,
    round_id: SOPHIE_INITIAL_ROUND_ID,
    package_id: packageId,
    prompt_text: INITIAL_SOPHIE_PROMPT_V1,
  });

  const metadata = {
    agent_id: SOPHIE_AGENT_ID,
    agent_display_name: SOPHIE_AGENT_DISPLAY_NAME,
    round_id: SOPHIE_INITIAL_ROUND_ID,
    package_id: packageId,
    filename: built.filename,
    created_at: now(),
  };

  await persistExport(packageInput.project_id, metadata);
  download(built.blob, built.filename);

  return metadata;
}


export function installSophieR001DownloadButton({
  documentObject = document,
  runExport = downloadInitialSophiePackageV1,
} = {}) {
  const button = documentObject.querySelector('#download-ai-package');
  const status = documentObject.querySelector('#ai-package-status');
  if (!button) return;

  button.textContent = 'Créer le ZIP pour Sophie';
  if (status) {
    status.textContent = 'Le ZIP contiendra les instructions V1 et toutes les photos actives compatibles.';
  }

  button.addEventListener('click', async event => {
    event.preventDefault();
    event.stopImmediatePropagation();
    button.disabled = true;
    if (status) status.textContent = 'Création du ZIP pour Sophie…';

    try {
      const metadata = await runExport();
      if (status) {
        status.textContent = `ZIP prêt : ${metadata.filename}`;
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      if (status) {
        status.textContent = `Impossible de créer le ZIP : ${message}`;
      }
    } finally {
      button.disabled = false;
    }
  }, { capture: true });
}


if (typeof window !== 'undefined' && typeof document !== 'undefined') {
  installSophieR001DownloadButton();
}
