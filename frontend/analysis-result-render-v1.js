import { getActiveProjectSnapshot } from './project-photo-store.js';


const FACE_ORDER = ['FRONT', 'RIGHT', 'LEFT', 'REAR'];
const RESULT_VIEW_ID = 'sophie-r001-result-view';
const RESULT_IMPORTED_EVENT = 'boldungo:analysis-result-v1-imported';
const SHELL_READY_EVENT = 'boldungo:photo-shell-ready';

let activeObjectUrls = [];


function photoNumber(photoId) {
  const match = String(photoId || '').match(/_(\d+)$/);
  return match ? Number(match[1]) : Number.MAX_SAFE_INTEGER;
}


export function sortPhotosForSophieR001(photos) {
  return [...photos].sort((left, right) => {
    const leftFace = FACE_ORDER.indexOf(left?.primary_face);
    const rightFace = FACE_ORDER.indexOf(right?.primary_face);
    const leftRank = leftFace === -1 ? FACE_ORDER.length : leftFace;
    const rightRank = rightFace === -1 ? FACE_ORDER.length : rightFace;
    return leftRank - rightRank
      || photoNumber(left?.photo_id) - photoNumber(right?.photo_id)
      || String(left?.photo_id || '').localeCompare(String(right?.photo_id || ''));
  });
}


export function latestPersistedSophieR001Result(project) {
  const imports = Array.isArray(project?.analysis_result_imports)
    ? project.analysis_result_imports
    : [];

  for (let index = imports.length - 1; index >= 0; index -= 1) {
    const document = imports[index]?.document;
    if (
      document?.schema_version === 'boldungo.exchange.v1'
      && document?.message_type === 'ANALYSIS_RESULT'
      && document?.project_id === project?.project_id
      && document?.agent_id === 'SOPHIE'
      && document?.agent_display_name === 'Sophie'
      && document?.round_id === 'R001'
    ) {
      return document;
    }
  }
  return null;
}


export function buildSophieR001QuestionViewModel(snapshot, result) {
  if (!snapshot?.project || !Array.isArray(snapshot?.photos)) {
    throw new Error('Projet actif ou photos indisponibles');
  }
  if (!result?.payload || !Array.isArray(result.payload.questions)) {
    throw new Error('RESULT Sophie R001 invalide pour le rendu');
  }

  const photos = sortPhotosForSophieR001(snapshot.photos);
  const photoIds = new Set(photos.map(photo => photo.photo_id));
  const questions = result.payload.questions;

  for (const question of questions) {
    if (question.scope !== 'PHOTO') continue;
    for (const photoId of question.photo_refs) {
      if (!photoIds.has(photoId)) {
        throw new Error(`Sophie référence une photo introuvable : ${photoId}`);
      }
    }
  }

  return {
    photos: photos.map(photo => ({
      photo,
      questions: questions.filter(question => (
        question.scope === 'PHOTO'
        && question.photo_refs.includes(photo.photo_id)
      )),
    })),
    global_questions: questions.filter(question => question.scope === 'GLOBAL'),
    no_questions: questions.length === 0,
  };
}


function releaseObjectUrls(urlApi = URL) {
  for (const url of activeObjectUrls) {
    urlApi.revokeObjectURL(url);
  }
  activeObjectUrls = [];
}


function element(documentObject, tagName, className, text = null) {
  const node = documentObject.createElement(tagName);
  if (className) node.className = className;
  if (text !== null) node.textContent = text;
  return node;
}


function questionNode(documentObject, question) {
  const card = element(documentObject, 'article', 'sophie-v1-question');
  card.dataset.questionId = question.question_id;

  if (question.subject_hint) {
    card.appendChild(
      element(documentObject, 'div', 'sophie-v1-question-subject', question.subject_hint),
    );
  }
  card.appendChild(
    element(documentObject, 'div', 'sophie-v1-question-text', question.question_text),
  );
  card.appendChild(
    element(documentObject, 'small', 'sophie-v1-question-id', question.question_id),
  );
  return card;
}


export function renderSophieR001ResultView(
  snapshot,
  result,
  {
    documentObject = document,
    urlApi = URL,
    eventTarget = globalThis.window,
  } = {},
) {
  const host = documentObject.getElementById(RESULT_VIEW_ID);
  if (!host) return false;

  releaseObjectUrls(urlApi);
  host.replaceChildren();
  host.hidden = false;
  host.dataset.state = 'ready';
  host.closest?.('.shell-survey-card')?.classList.add('has-sophie-result');

  let model;
  try {
    model = buildSophieR001QuestionViewModel(snapshot, result);
  } catch (error) {
    host.dataset.state = 'error';
    host.appendChild(
      element(
        documentObject,
        'p',
        'sophie-v1-render-error',
        error instanceof Error ? error.message : String(error),
      ),
    );
    return false;
  }

  if (model.no_questions) {
    host.appendChild(
      element(
        documentObject,
        'p',
        'sophie-v1-no-questions',
        'Sophie n’a aucune question pour ce round.',
      ),
    );
  }

  for (const item of model.photos) {
    const block = element(documentObject, 'section', 'sophie-v1-photo-block');
    const image = element(documentObject, 'img', 'sophie-v1-photo-image');
    image.alt = item.photo.photo_id;
    if (item.photo.blob instanceof Blob) {
      const url = urlApi.createObjectURL(item.photo.blob);
      activeObjectUrls.push(url);
      image.src = url;
    }
    block.appendChild(image);

    const meta = element(documentObject, 'div', 'sophie-v1-photo-meta');
    meta.appendChild(
      element(documentObject, 'strong', 'sophie-v1-photo-id', item.photo.photo_id),
    );
    if (item.photo.original_filename) {
      meta.appendChild(
        element(
          documentObject,
          'small',
          'sophie-v1-photo-filename',
          item.photo.original_filename,
        ),
      );
    }
    block.appendChild(meta);

    const questions = element(documentObject, 'div', 'sophie-v1-photo-questions');
    for (const question of item.questions) {
      questions.appendChild(questionNode(documentObject, question));
    }
    block.appendChild(questions);
    host.appendChild(block);
  }

  if (model.global_questions.length) {
    const globalSection = element(documentObject, 'section', 'sophie-v1-global-questions');
    globalSection.appendChild(
      element(documentObject, 'h3', null, 'Questions générales'),
    );
    for (const question of model.global_questions) {
      globalSection.appendChild(questionNode(documentObject, question));
    }
    host.appendChild(globalSection);
  }

  eventTarget?.dispatchEvent?.(new Event('boldungo:analysis-result-v1-rendered'));
  return true;
}


export async function refreshSophieR001ResultView({
  getSnapshot = getActiveProjectSnapshot,
  documentObject = document,
  urlApi = URL,
  eventTarget = globalThis.window,
} = {}) {
  const host = documentObject.getElementById(RESULT_VIEW_ID);
  if (!host) return false;

  const snapshot = await getSnapshot();
  const result = latestPersistedSophieR001Result(snapshot.project);
  if (!result) {
    releaseObjectUrls(urlApi);
    host.replaceChildren();
    host.hidden = true;
    delete host.dataset.state;
    host.closest?.('.shell-survey-card')?.classList.remove('has-sophie-result');
    return false;
  }

  return renderSophieR001ResultView(snapshot, result, {
    documentObject,
    urlApi,
    eventTarget,
  });
}


export function installSophieR001ResultRenderer({
  eventTarget = globalThis.window,
  refresh = refreshSophieR001ResultView,
} = {}) {
  if (!eventTarget?.addEventListener) return;
  eventTarget.addEventListener(RESULT_IMPORTED_EVENT, () => { void refresh(); });
  eventTarget.addEventListener(SHELL_READY_EVENT, () => { void refresh(); });
  void refresh();
}


if (typeof window !== 'undefined' && typeof document !== 'undefined') {
  installSophieR001ResultRenderer();
}
