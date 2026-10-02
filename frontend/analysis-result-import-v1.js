import {
  appendAnalysisResultImport,
  getActiveProject,
} from './project-photo-store.js';
import {
  isBoldungoExchangeV1,
  validateAnalysisResultV1,
} from './analysis-result-validator-v1.js';


export const SOPHIE_R001_AGENT_ID = 'SOPHIE';
export const SOPHIE_R001_AGENT_DISPLAY_NAME = 'Sophie';
export const SOPHIE_R001_ROUND_ID = 'R001';


function rejected(reason) {
  return { valid: false, reason };
}


export function validateSophieR001ResultForProject(document, project) {
  const structural = validateAnalysisResultV1(document);
  if (!structural.valid) {
    return rejected(`contrat V1 invalide : ${structural.reason}`);
  }

  if (!project || typeof project !== 'object') {
    return rejected('aucun projet actif');
  }
  if (document.project_id !== project.project_id) {
    return rejected(
      `mauvais project_id : attendu ${project.project_id}, reçu ${document.project_id}`,
    );
  }
  if (document.agent_id !== SOPHIE_R001_AGENT_ID) {
    return rejected(
      `mauvais agent_id : attendu ${SOPHIE_R001_AGENT_ID}, reçu ${document.agent_id}`,
    );
  }
  if (document.agent_display_name !== SOPHIE_R001_AGENT_DISPLAY_NAME) {
    return rejected(
      `mauvais agent_display_name : attendu ${SOPHIE_R001_AGENT_DISPLAY_NAME}, reçu ${document.agent_display_name}`,
    );
  }
  if (document.round_id !== SOPHIE_R001_ROUND_ID) {
    return rejected(
      `mauvais round_id : attendu ${SOPHIE_R001_ROUND_ID}, reçu ${document.round_id}`,
    );
  }

  const exports = Array.isArray(project.analysis_package_exports)
    ? project.analysis_package_exports
    : [];
  const knownPackage = exports.some(item => (
    item?.agent_id === document.agent_id
    && item?.round_id === document.round_id
    && item?.package_id === document.package_id
  ));
  if (!knownPackage) {
    return rejected(`package_id inconnu : ${document.package_id}`);
  }

  return { valid: true, reason: null };
}


export async function importSophieR001AnalysisResult(
  document,
  {
    getActiveProjectFn = getActiveProject,
    persistResultFn = appendAnalysisResultImport,
    now = () => new Date().toISOString(),
  } = {},
) {
  const project = await getActiveProjectFn();
  const validation = validateSophieR001ResultForProject(document, project);
  if (!validation.valid) {
    throw new Error(validation.reason);
  }

  const importedAt = now();
  await persistResultFn(project.project_id, document, importedAt);
  return {
    project_id: project.project_id,
    package_id: document.package_id,
    imported_at: importedAt,
  };
}


function parseTextareaDocument(input) {
  const raw = String(input?.value ?? '').trim();
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}


export function installSophieR001ResultImport({
  documentObject = document,
  importResult = importSophieR001AnalysisResult,
  eventTarget = globalThis.window,
} = {}) {
  const button = documentObject.querySelector('#import-analysis');
  const input = documentObject.querySelector('#external-analysis');
  const status = documentObject.querySelector('#status');
  if (!button || !input) return;

  button.addEventListener('click', async event => {
    const parsed = parseTextareaDocument(input);
    if (!isBoldungoExchangeV1(parsed)) {
      return;
    }

    event.preventDefault();
    event.stopImmediatePropagation();
    button.disabled = true;

    try {
      await importResult(parsed);
      if (status) status.textContent = 'Résultat Sophie R001 validé.';
      eventTarget?.dispatchEvent?.(new Event('boldungo:analysis-result-v1-imported'));
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      if (status) status.textContent = `Résultat Sophie R001 refusé : ${message}`;
    } finally {
      button.disabled = false;
    }
  }, { capture: true });
}


if (typeof window !== 'undefined' && typeof document !== 'undefined') {
  installSophieR001ResultImport();
}
