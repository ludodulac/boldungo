import {
  getActiveProjectSnapshot,
  upsertAnalysisAnswerDraft,
} from './project-photo-store.js';
import {
  latestPersistedSophieR001Result,
} from './analysis-result-render-v1.js';


const RESULT_RENDERED_EVENT = 'boldungo:analysis-result-v1-rendered';
const RESULT_IMPORTED_EVENT = 'boldungo:analysis-result-v1-imported';


function sameResultIdentity(draft, result) {
  return (
    draft?.agent_id === result?.agent_id
    && draft?.round_id === result?.round_id
    && draft?.package_id === result?.package_id
  );
}


export function answerDraftsForResult(project, result) {
  const drafts = Array.isArray(project?.analysis_answer_drafts)
    ? project.analysis_answer_drafts
    : [];
  return drafts.filter(draft => sameResultIdentity(draft, result));
}


export function validateAnswerDraftForQuestion(question, draft) {
  if (!question) throw new Error(`Question introuvable : ${draft?.question_id ?? 'inconnue'}`);
  if (!draft || draft.question_id !== question.question_id) {
    throw new Error('question_id de réponse incohérent');
  }

  if (draft.answer_state === 'UNKNOWN') {
    if (!question.allow_unknown) {
      throw new Error(`${question.question_id} n’autorise pas « Je ne sais pas »`);
    }
    if (draft.value !== null) {
      throw new Error(`${question.question_id} UNKNOWN exige value=null`);
    }
    return true;
  }

  if (draft.answer_state !== 'ANSWERED') {
    throw new Error(`${question.question_id} answer_state invalide`);
  }
  if (typeof draft.value !== 'string' || !draft.value.trim()) {
    throw new Error(`${question.question_id} ANSWERED exige une valeur non vide`);
  }

  if (question.answer_type === 'YES_NO') {
    if (!['YES', 'NO'].includes(draft.value)) {
      throw new Error(`${question.question_id} YES_NO exige YES ou NO`);
    }
  } else if (question.answer_type === 'SINGLE_CHOICE') {
    const allowed = new Set(question.choices.map(choice => choice.value));
    if (!allowed.has(draft.value)) {
      throw new Error(`${question.question_id} exige un choice.value déclaré`);
    }
  } else if (question.answer_type === 'FREE_TEXT') {
    if (!draft.value.trim()) {
      throw new Error(`${question.question_id} FREE_TEXT exige un texte non vide`);
    }
  } else {
    throw new Error(`${question.question_id} answer_type invalide`);
  }

  return true;
}


export function buildHumanAnswersV1(
  result,
  drafts,
  {
    createdAt = new Date().toISOString(),
  } = {},
) {
  if (
    result?.schema_version !== 'boldungo.exchange.v1'
    || result?.message_type !== 'ANALYSIS_RESULT'
    || !Array.isArray(result?.payload?.questions)
  ) {
    throw new Error('ANALYSIS_RESULT actif invalide');
  }
  if (
    typeof createdAt !== 'string'
    || !createdAt.endsWith('Z')
    || Number.isNaN(Date.parse(createdAt))
  ) {
    throw new Error('created_at doit être une date ISO 8601 UTC');
  }

  const activeDrafts = drafts.filter(draft => sameResultIdentity(draft, result));
  const byQuestion = new Map();
  const questions = new Map(
    result.payload.questions.map(question => [question.question_id, question]),
  );

  for (const draft of activeDrafts) {
    const question = questions.get(draft.question_id);
    if (!question) {
      throw new Error(`Réponse persistée pour une question inconnue : ${draft.question_id}`);
    }
    if (byQuestion.has(draft.question_id)) {
      throw new Error(`Réponse dupliquée : ${draft.question_id}`);
    }
    validateAnswerDraftForQuestion(question, draft);
    byQuestion.set(draft.question_id, draft);
  }

  const answers = [];
  for (const question of result.payload.questions) {
    const draft = byQuestion.get(question.question_id);
    if (!draft) continue;
    answers.push({
      question_id: question.question_id,
      answer_state: draft.answer_state,
      value: draft.value,
      note: null,
    });
  }

  const document = {
    schema_version: 'boldungo.exchange.v1',
    message_type: 'HUMAN_ANSWERS',
    project_id: result.project_id,
    agent_id: result.agent_id,
    agent_display_name: result.agent_display_name,
    round_id: result.round_id,
    package_id: result.package_id,
    created_at: createdAt,
    payload: { answers },
  };

  return {
    filename: `BOLDUNGO_${result.project_id}_${result.agent_id}_${result.round_id}_ANSWERS.json`,
    document,
  };
}


export function makeAnswerDraft(result, question, answerState, value) {
  const draft = {
    agent_id: result.agent_id,
    round_id: result.round_id,
    package_id: result.package_id,
    question_id: question.question_id,
    answer_state: answerState,
    value,
  };
  validateAnswerDraftForQuestion(question, draft);
  return draft;
}


export function syncQuestionAnswerOccurrences(documentObject, questionId, draft) {
  const cards = documentObject.querySelectorAll(
    `.sophie-v1-question[data-question-id="${questionId}"]`,
  );
  for (const card of cards) {
    const buttons = card.querySelectorAll('[data-answer-value], [data-answer-unknown]');
    for (const button of buttons) {
      const selected = draft?.answer_state === 'UNKNOWN'
        ? button.hasAttribute('data-answer-unknown')
        : (
          draft?.answer_state === 'ANSWERED'
          && button.getAttribute('data-answer-value') === draft.value
        );
      button.dataset.selected = selected ? 'true' : 'false';
      button.setAttribute('aria-pressed', selected ? 'true' : 'false');
    }
    const text = card.querySelector('[data-answer-text]');
    if (text) {
      text.value = draft?.answer_state === 'ANSWERED' ? draft.value : '';
    }
  }
}


function updateProgress(documentObject, result, drafts) {
  const node = documentObject.querySelector('#sophie-v1-answer-progress');
  if (!node) return;
  const unique = new Set(
    drafts
      .filter(draft => sameResultIdentity(draft, result))
      .map(draft => draft.question_id),
  );
  node.textContent = `${unique.size} réponse(s) sur ${result.payload.questions.length}`;
}


function createChoiceButton(documentObject, label, value, onAnswer) {
  const button = documentObject.createElement('button');
  button.type = 'button';
  button.className = 'sophie-v1-answer-choice';
  button.textContent = label;
  button.dataset.answerValue = value;
  button.setAttribute('aria-pressed', 'false');
  button.addEventListener('click', () => { void onAnswer('ANSWERED', value); });
  return button;
}


function createControlsForQuestion(documentObject, question, onAnswer) {
  const controls = documentObject.createElement('div');
  controls.className = 'sophie-v1-answer-controls';

  if (question.answer_type === 'YES_NO') {
    controls.append(
      createChoiceButton(documentObject, 'Oui', 'YES', onAnswer),
      createChoiceButton(documentObject, 'Non', 'NO', onAnswer),
    );
  } else if (question.answer_type === 'SINGLE_CHOICE') {
    for (const choice of question.choices) {
      controls.appendChild(
        createChoiceButton(documentObject, choice.label, choice.value, onAnswer),
      );
    }
  } else if (question.answer_type === 'FREE_TEXT') {
    const input = documentObject.createElement('input');
    input.type = 'text';
    input.className = 'sophie-v1-answer-text';
    input.dataset.answerText = 'true';
    input.placeholder = 'Votre réponse…';
    input.addEventListener('change', () => {
      const value = input.value.trim();
      if (value) void onAnswer('ANSWERED', value);
    });
    controls.appendChild(input);
  }

  if (question.allow_unknown) {
    const unknown = documentObject.createElement('button');
    unknown.type = 'button';
    unknown.className = 'sophie-v1-answer-unknown';
    unknown.textContent = 'Je ne sais pas';
    unknown.dataset.answerUnknown = 'true';
    unknown.setAttribute('aria-pressed', 'false');
    unknown.addEventListener('click', () => { void onAnswer('UNKNOWN', null); });
    controls.appendChild(unknown);
  }

  return controls;
}


export function downloadHumanAnswersJson(blobDocument, {
  documentObject = document,
  urlApi = URL,
} = {}) {
  const bytes = `${JSON.stringify(blobDocument.document, null, 2)}\n`;
  const blob = new Blob([bytes], { type: 'application/json' });
  const url = urlApi.createObjectURL(blob);
  const link = documentObject.createElement('a');
  link.href = url;
  link.download = blobDocument.filename;
  documentObject.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => urlApi.revokeObjectURL(url), 1000);
}


export async function refreshSophieR001AnswerUi({
  getSnapshot = getActiveProjectSnapshot,
  persistDraft = upsertAnalysisAnswerDraft,
  documentObject = document,
  download = downloadHumanAnswersJson,
} = {}) {
  const host = documentObject.getElementById('sophie-r001-result-view');
  if (!host || host.hidden || host.dataset.state !== 'ready') return false;

  const snapshot = await getSnapshot();
  const result = latestPersistedSophieR001Result(snapshot.project);
  if (!result) return false;

  host.querySelectorAll('.sophie-v1-answer-controls, .sophie-v1-answer-export')
    .forEach(node => node.remove());

  let drafts = answerDraftsForResult(snapshot.project, result);
  const draftMap = new Map(drafts.map(draft => [draft.question_id, draft]));
  const questionMap = new Map(
    result.payload.questions.map(question => [question.question_id, question]),
  );

  for (const [questionId, question] of questionMap) {
    const occurrences = host.querySelectorAll(
      `.sophie-v1-question[data-question-id="${questionId}"]`,
    );
    const onAnswer = async (answerState, value) => {
      try {
        const draft = makeAnswerDraft(result, question, answerState, value);
        await persistDraft(result.project_id, draft);
        const existingIndex = drafts.findIndex(item => item.question_id === questionId);
        if (existingIndex >= 0) drafts[existingIndex] = draft;
        else drafts.push(draft);
        syncQuestionAnswerOccurrences(documentObject, questionId, draft);
        updateProgress(documentObject, result, drafts);
        const status = documentObject.querySelector('.sophie-v1-answer-status');
        if (status) status.textContent = '';
      } catch (error) {
        const status = documentObject.querySelector('.sophie-v1-answer-status');
        if (status) {
          status.textContent = `Réponse non enregistrée : ${error instanceof Error ? error.message : String(error)}`;
        }
      }
    };
    for (const occurrence of occurrences) {
      occurrence.appendChild(
        createControlsForQuestion(documentObject, question, onAnswer),
      );
    }
    const restored = draftMap.get(questionId);
    if (restored) {
      validateAnswerDraftForQuestion(question, restored);
      syncQuestionAnswerOccurrences(documentObject, questionId, restored);
    }
  }

  const footer = documentObject.createElement('section');
  footer.className = 'sophie-v1-answer-export';

  const progress = documentObject.createElement('div');
  progress.id = 'sophie-v1-answer-progress';
  progress.className = 'sophie-v1-answer-progress';
  footer.appendChild(progress);

  const exportButton = documentObject.createElement('button');
  exportButton.type = 'button';
  exportButton.className = 'sophie-v1-answer-download';
  exportButton.textContent = 'Télécharger mes réponses pour Sophie';
  footer.appendChild(exportButton);

  const status = documentObject.createElement('p');
  status.className = 'sophie-v1-answer-status';
  status.setAttribute('role', 'status');
  footer.appendChild(status);

  exportButton.addEventListener('click', async () => {
    try {
      const current = await getSnapshot();
      const currentResult = latestPersistedSophieR001Result(current.project);
      if (!currentResult) throw new Error('RESULT Sophie R001 introuvable');
      const currentDrafts = answerDraftsForResult(current.project, currentResult);
      const built = buildHumanAnswersV1(currentResult, currentDrafts);
      download(built, { documentObject });
      status.textContent = `Réponses prêtes : ${built.filename}`;
    } catch (error) {
      status.textContent = `Export impossible : ${error instanceof Error ? error.message : String(error)}`;
    }
  });

  host.appendChild(footer);
  updateProgress(documentObject, result, drafts);
  return true;
}


export function installSophieR001AnswerUi({
  eventTarget = globalThis.window,
  refresh = refreshSophieR001AnswerUi,
} = {}) {
  if (!eventTarget?.addEventListener) return;
  eventTarget.addEventListener(RESULT_RENDERED_EVENT, () => { void refresh(); });
  eventTarget.addEventListener(RESULT_IMPORTED_EVENT, () => { void refresh(); });
  void refresh();
}


if (typeof window !== 'undefined' && typeof document !== 'undefined') {
  installSophieR001AnswerUi();
}
