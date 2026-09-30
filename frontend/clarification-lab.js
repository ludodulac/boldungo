import {
  activeQuestionQueue,
  applyHumanAnswer,
  applyPreexistingHumanFacts,
  escalateRequestedPhoto,
  evaluateClarificationGate,
  markUnknown,
  normalizeClarifications,
  recomputeDependencies,
  resolveConflict,
  setUnknownStrategy,
} from './clarification-engine.js';
import {
  getActiveProjectSnapshot,
  updateProjectClarificationState,
} from './project-photo-store.js';

const params = new URLSearchParams(window.location.search);
const fixtureMode = params.get('clarification-lab') === 'real-house-5';
const lab = document.querySelector('#clarification-lab');
const gateEl = document.querySelector('#clarification-gate');
const projectEl = document.querySelector('#clarification-project');
const progressEl = document.querySelector('#clarification-progress');
const questionEl = document.querySelector('#clarification-question');
const choicesEl = document.querySelector('#clarification-choices');
const unknownButton = document.querySelector('#clarification-unknown');
const requestPhotoButton = document.querySelector('#clarification-request-photo');
const deferButton = document.querySelector('#clarification-defer');
const conflictKeepButton = document.querySelector('#clarification-conflict-keep');
const summaryEl = document.querySelector('#clarification-summary');
const photoSpecEl = document.querySelector('#clarification-photo-spec');
const errorEl = document.querySelector('#clarification-error');

let fixture = null;
let project = null;
let clarifications = [];
let humanFacts = [];
let currentItem = null;
let savePromise = Promise.resolve();
window.boldungoClarificationSavePromise = savePromise;

function escapeText(value) {
  return String(value ?? '');
}

function setError(message = '') {
  if (errorEl) errorEl.textContent = message;
}

function persistState() {
  if (!project) return Promise.resolve();
  const operation = updateProjectClarificationState(project.project_id, {
    clarifications,
    humanFacts,
    fixtureId: project.clarification_fixture_id || fixture?.fixture_id,
  }).then(updated => {
    project = updated;
    return updated;
  });
  savePromise = operation.catch(error => {
    console.error(error);
    setError('Erreur de sauvegarde des clarifications.');
    throw error;
  });
  window.boldungoClarificationSavePromise = savePromise;
  return savePromise;
}

function priorityIndex(value) {
  return [
    'TARGET_BOUNDARY',
    'OBJECT_OWNERSHIP',
    'TOPOLOGY',
    'SOLID_VOID',
    'ACCESS',
    'LEVEL_CONTINUITY',
    'MATERIAL',
    'DETAIL',
  ].indexOf(value);
}

function activeSpecialItem(items, state) {
  return items
    .filter(item => item.answer_state === state)
    .sort((a, b) => priorityIndex(a.priority) - priorityIndex(b.priority) || a.catalog_order - b.catalog_order)[0] || null;
}

function unknownFollowup(items) {
  return items
    .filter(item => (
      item.answer_state === 'UNKNOWN'
      && !item.unknown_strategy
      && (item.requested_photo_spec || item.defer_policy === 'ALLOWED')
    ))
    .sort((a, b) => priorityIndex(a.priority) - priorityIndex(b.priority) || a.catalog_order - b.catalog_order)[0] || null;
}

function chooseCurrentItem(items) {
  return activeSpecialItem(items, 'CONFLICT')
    || activeSpecialItem(items, 'PHOTO_REQUESTED')
    || unknownFollowup(items)
    || activeQuestionQueue(items)[0]
    || null;
}

function choiceButton(choice, item) {
  const button = document.createElement('button');
  button.type = 'button';
  button.className = 'clarification-choice';
  button.dataset.clarificationAnswer = typeof choice === 'string' ? choice : choice.value;
  button.textContent = typeof choice === 'string' ? choice : choice.label;
  button.addEventListener('click', async () => {
    setError('');
    const result = applyHumanAnswer(
      clarifications,
      humanFacts,
      item.clarification_id,
      button.dataset.clarificationAnswer,
    );
    clarifications = result.clarifications;
    humanFacts = result.human_facts;
    await persistState();
    render();
  });
  return button;
}

function renderQuestion(item) {
  choicesEl?.replaceChildren();
  if (!item) {
    questionEl.textContent = 'Aucune question active.';
    if (progressEl) progressEl.textContent = 'File de clarification terminée pour les éléments actifs.';
    return;
  }

  if (progressEl) {
    const answered = clarifications.filter(candidate => (
      candidate.answer_state === 'RESOLVED' || candidate.answer_state === 'NOT_APPLICABLE'
    )).length;
    progressEl.textContent = `Question ${Math.min(answered + 1, clarifications.length)} / ${clarifications.length} · ${item.priority}`;
  }

  questionEl.textContent = item.question_text;

  if (item.answer_state === 'CONFLICT') {
    const note = document.createElement('p');
    note.className = 'clarification-conflict';
    note.textContent = 'Conflit : la réponse humaine et l’observation photo récupérée ne concordent pas.';
    choicesEl.appendChild(note);
    conflictKeepButton.hidden = false;
    unknownButton.hidden = true;
    requestPhotoButton.hidden = !item.requested_photo_spec;
    deferButton.hidden = true;
    return;
  }

  conflictKeepButton.hidden = true;

  if (item.answer_state === 'PHOTO_REQUESTED') {
    const spec = item.requested_photo_spec;
    photoSpecEl.hidden = false;
    photoSpecEl.textContent = `Photo demandée — ${spec.purpose}. Position : ${spec.camera_position_hint}. À voir : ${spec.what_must_be_visible}.`;
    unknownButton.hidden = true;
    requestPhotoButton.hidden = true;
    deferButton.hidden = true;
    return;
  }

  photoSpecEl.hidden = true;

  if (item.answer_state === 'UNKNOWN') {
    const note = document.createElement('p');
    note.className = 'clarification-unknown-state';
    note.textContent = 'Réponse conservée : JE NE SAIS PAS. Aucune valeur géométrique n’est inventée.';
    choicesEl.appendChild(note);
    unknownButton.hidden = true;
    requestPhotoButton.hidden = !item.requested_photo_spec;
    deferButton.hidden = item.defer_policy !== 'ALLOWED';
    return;
  }

  unknownButton.hidden = false;
  requestPhotoButton.hidden = true;
  deferButton.hidden = true;

  if (item.question_type === 'HUMAN_FACT_TEXT') {
    const input = document.createElement('input');
    input.type = 'text';
    input.className = 'clarification-text-answer';
    input.placeholder = 'Votre réponse…';
    const submit = document.createElement('button');
    submit.type = 'button';
    submit.className = 'clarification-choice';
    submit.textContent = 'Enregistrer';
    submit.addEventListener('click', async () => {
      const value = input.value.trim();
      if (!value) {
        setError('Saisissez une réponse ou choisissez « Je ne sais pas ».');
        return;
      }
      const result = applyHumanAnswer(clarifications, humanFacts, item.clarification_id, value);
      clarifications = result.clarifications;
      humanFacts = result.human_facts;
      await persistState();
      render();
    });
    choicesEl.append(input, submit);
  } else {
    for (const choice of item.choices || []) choicesEl.appendChild(choiceButton(choice, item));
  }
}

function renderSummary() {
  if (!summaryEl) return;
  summaryEl.replaceChildren();
  const visible = clarifications.filter(item => item.answer_state !== 'OPEN' && item.answer_state !== 'NOT_APPLICABLE');
  if (!visible.length) {
    const empty = document.createElement('small');
    empty.textContent = 'Aucune réponse enregistrée.';
    summaryEl.appendChild(empty);
    return;
  }
  for (const item of visible.slice(-6)) {
    const row = document.createElement('div');
    row.className = 'clarification-summary-row';
    const value = item.answer_state === 'UNKNOWN'
      ? 'JE NE SAIS PAS'
      : item.answer_state === 'PHOTO_REQUESTED'
        ? 'PHOTO DEMANDÉE'
        : item.answer_state === 'CONFLICT'
          ? 'CONFLIT'
          : item.answer;
    row.textContent = `${item.clarification_id} · ${escapeText(value)}`;
    summaryEl.appendChild(row);
  }
}

function renderGate() {
  const gate = evaluateClarificationGate(clarifications);
  if (!gateEl) return;
  gateEl.dataset.gate = gate.gate;
  gateEl.dataset.geometryScope = gate.geometry_scope || '';
  if (gate.gate === 'BLOCKED') {
    gateEl.textContent = 'CLARIFICATION : BLOQUÉ';
  } else if (gate.geometry_scope === 'PARTIAL') {
    gateEl.textContent = `CLARIFICATION : PRÊT — PARTIEL · différé : ${gate.deferred_subjects.join(', ')}`;
  } else {
    gateEl.textContent = 'CLARIFICATION : PRÊT — COMPLET';
  }
}

function render() {
  if (!fixtureMode || !lab) return;
  setError('');
  if (!project) {
    lab.hidden = true;
    projectEl.textContent = 'Aucun projet actif — créez ou ouvrez un projet. La fixture LAB ne crée jamais de faux projet utilisateur.';
    gateEl.textContent = 'CLARIFICATION : BLOQUÉ';
    gateEl.dataset.gate = 'BLOCKED';
    progressEl.textContent = '';
    questionEl.textContent = 'En attente d’un projet utilisateur.';
    choicesEl.replaceChildren();
    summaryEl.replaceChildren();
    unknownButton.hidden = true;
    requestPhotoButton.hidden = true;
    deferButton.hidden = true;
    conflictKeepButton.hidden = true;
    photoSpecEl.hidden = true;
    return;
  }

  lab.hidden = false;
  clarifications = recomputeDependencies(clarifications);
  projectEl.textContent = `Projet : ${project.project_name} · fixture locale real-house-5`;
  renderGate();
  currentItem = chooseCurrentItem(clarifications);
  renderQuestion(currentItem);
  renderSummary();
  lab.dataset.projectId = project.project_id;
  lab.dataset.fixtureId = project.clarification_fixture_id || '';
  lab.dataset.currentClarificationId = currentItem?.clarification_id || '';
}

async function loadFixture() {
  if (fixture) return fixture;
  const response = await fetch('./benchmarks/real-house-5/clarifications-v1.json', { cache: 'no-store' });
  if (!response.ok) throw new Error(`Fixture clarification introuvable: HTTP ${response.status}`);
  fixture = await response.json();
  return fixture;
}

async function syncProject() {
  if (!fixtureMode || !lab) return;
  try {
    await loadFixture();
    const snapshot = await getActiveProjectSnapshot();
    project = snapshot.project;
    if (!project) {
      clarifications = [];
      humanFacts = [];
      render();
      window.boldungoClarificationLabReady = true;
      window.dispatchEvent(new CustomEvent('boldungo:clarification-lab-ready'));
      return;
    }

    humanFacts = Array.isArray(project.human_facts) ? project.human_facts : [];
    if (!Array.isArray(project.clarifications) || !project.clarifications.length) {
      const seeded = applyPreexistingHumanFacts(
        normalizeClarifications(fixture.clarifications),
        humanFacts,
      );
      clarifications = seeded.clarifications;
      humanFacts = seeded.human_facts;
      project = await updateProjectClarificationState(project.project_id, {
        clarifications,
        humanFacts,
        fixtureId: fixture.fixture_id,
      });
    } else {
      clarifications = normalizeClarifications(project.clarifications);
    }
    render();
    window.boldungoClarificationLabReady = true;
    window.dispatchEvent(new CustomEvent('boldungo:clarification-lab-ready', {
      detail: { project_id: project.project_id, fixture_id: project.clarification_fixture_id || null },
    }));
  } catch (error) {
    console.error(error);
    setError(String(error?.message || error));
  }
}

unknownButton?.addEventListener('click', async () => {
  if (!currentItem) return;
  clarifications = markUnknown(clarifications, currentItem.clarification_id);
  await persistState();
  render();
});

requestPhotoButton?.addEventListener('click', async () => {
  if (!currentItem) return;
  clarifications = escalateRequestedPhoto(clarifications, currentItem.clarification_id);
  await persistState();
  render();
});

deferButton?.addEventListener('click', async () => {
  if (!currentItem) return;
  clarifications = setUnknownStrategy(
    clarifications,
    currentItem.clarification_id,
    'DEFER_AFFECTED_GEOMETRY',
  );
  await persistState();
  render();
});

conflictKeepButton?.addEventListener('click', async () => {
  if (!currentItem) return;
  clarifications = resolveConflict(clarifications, currentItem.clarification_id, 'KEEP_HUMAN');
  await persistState();
  render();
});

if (fixtureMode && lab) {
  window.addEventListener('boldungo:project-photo-intake-ready', syncProject);
  if (document.documentElement.dataset.projectPhotoIntakeReady === 'true') {
    syncProject();
  }
}
