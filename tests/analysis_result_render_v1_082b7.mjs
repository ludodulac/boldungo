import assert from 'node:assert/strict';

import {
  buildSophieR001QuestionViewModel,
  installSophieR001ResultRenderer,
  latestPersistedSophieR001Result,
  sortPhotosForSophieR001,
} from '../frontend/analysis-result-render-v1.js';
import {
  installSophieR001ResultImport,
} from '../frontend/analysis-result-import-v1.js';


function photo(photo_id, primary_face) {
  return {
    photo_id,
    primary_face,
    original_filename: `${photo_id.toLowerCase()}.jpg`,
    blob: new Blob([photo_id]),
  };
}


function resultWithQuestions(questions) {
  return {
    schema_version: 'boldungo.exchange.v1',
    message_type: 'ANALYSIS_RESULT',
    project_id: 'PROJECT_A',
    agent_id: 'SOPHIE',
    agent_display_name: 'Sophie',
    round_id: 'R001',
    package_id: 'PKG_550e8400-e29b-41d4-a716-446655440000',
    created_at: '2026-10-02T10:00:00Z',
    payload: {
      analysis: {
        observations: [],
        human_facts: [],
        entities: [],
        relations: [],
        uncertainties: [],
      },
      questions,
    },
  };
}


const snapshot = {
  project: { project_id: 'PROJECT_A' },
  photos: [
    photo('LEFT_002', 'LEFT'),
    photo('REAR_001', 'REAR'),
    photo('FRONT_002', 'FRONT'),
    photo('RIGHT_001', 'RIGHT'),
    photo('LEFT_001', 'LEFT'),
    photo('FRONT_001', 'FRONT'),
  ],
};

const frontQuestion = {
  question_id: 'Q001',
  scope: 'PHOTO',
  photo_refs: ['FRONT_001'],
  subject_hint: 'Ouverture haute',
  question_text: 'Cette ouverture est-elle une fenêtre ?',
};

const leftQuestion = {
  question_id: 'Q002',
  scope: 'PHOTO',
  photo_refs: ['LEFT_001'],
  subject_hint: 'Escalier visible',
  question_text: 'Le dessous de l’escalier est-il plein ?',
};

const multiQuestion = {
  question_id: 'Q003',
  scope: 'PHOTO',
  photo_refs: ['FRONT_002', 'LEFT_002'],
  subject_hint: 'Même volume visible sur deux vues',
  question_text: 'Ces deux vues montrent-elles le même volume ?',
};

const globalQuestion = {
  question_id: 'Q004',
  scope: 'GLOBAL',
  photo_refs: [],
  subject_hint: null,
  question_text: 'Connaissez-vous le matériau de toiture ?',
};

{
  const ordered = sortPhotosForSophieR001(snapshot.photos);
  assert.deepEqual(
    ordered.map(item => item.photo_id),
    ['FRONT_001', 'FRONT_002', 'RIGHT_001', 'LEFT_001', 'LEFT_002', 'REAR_001'],
  );
}

{
  const result = resultWithQuestions([
    frontQuestion,
    leftQuestion,
    multiQuestion,
    globalQuestion,
  ]);
  const model = buildSophieR001QuestionViewModel(snapshot, result);
  const byPhoto = Object.fromEntries(
    model.photos.map(item => [
      item.photo.photo_id,
      item.questions.map(question => question.question_id),
    ]),
  );

  assert.deepEqual(byPhoto.FRONT_001, ['Q001']);
  assert.deepEqual(byPhoto.LEFT_001, ['Q002']);
  assert.deepEqual(byPhoto.FRONT_002, ['Q003']);
  assert.deepEqual(byPhoto.LEFT_002, ['Q003']);
  assert.deepEqual(byPhoto.RIGHT_001, []);
  assert.deepEqual(byPhoto.REAR_001, []);
  assert.deepEqual(
    model.global_questions.map(question => question.question_id),
    ['Q004'],
  );
  assert.equal(model.no_questions, false);
}

{
  const model = buildSophieR001QuestionViewModel(snapshot, resultWithQuestions([]));
  assert.equal(model.no_questions, true);
  assert.equal(model.photos.length, 6);
  assert.deepEqual(model.global_questions, []);
  assert(model.photos.every(item => item.questions.length === 0));
}

{
  const bad = resultWithQuestions([{
    question_id: 'Q001',
    scope: 'PHOTO',
    photo_refs: ['FRONT_999'],
    subject_hint: 'Zone',
    question_text: 'Question impossible',
  }]);
  assert.throws(
    () => buildSophieR001QuestionViewModel(snapshot, bad),
    /Sophie référence une photo introuvable : FRONT_999/,
  );
}

{
  const older = resultWithQuestions([frontQuestion]);
  older.package_id = 'PKG_6ba7b810-9dad-41d1-80b4-00c04fd430c8';
  const latest = resultWithQuestions([leftQuestion]);
  const project = {
    project_id: 'PROJECT_A',
    analysis_result_imports: [
      { imported_at: '2026-10-02T09:00:00Z', document: older },
      { imported_at: '2026-10-02T10:00:00Z', document: latest },
    ],
  };
  assert.strictEqual(latestPersistedSophieR001Result(project), latest);
}

{
  const eventTarget = new EventTarget();
  let refreshCount = 0;
  installSophieR001ResultRenderer({
    eventTarget,
    refresh: async () => { refreshCount += 1; },
  });
  await Promise.resolve();
  const initialCount = refreshCount;
  eventTarget.dispatchEvent(new Event('boldungo:analysis-result-v1-imported'));
  await Promise.resolve();
  assert.equal(refreshCount, initialCount + 1);
  eventTarget.dispatchEvent(new Event('boldungo:photo-shell-ready'));
  await Promise.resolve();
  assert.equal(refreshCount, initialCount + 2);
}

function fakeImportDom(raw) {
  const status = { textContent: '' };
  const input = { value: raw };
  const button = {
    disabled: false,
    listener: null,
    addEventListener(type, listener) {
      assert.equal(type, 'click');
      this.listener = listener;
    },
  };
  return {
    status,
    button,
    documentObject: {
      querySelector(selector) {
        if (selector === '#import-analysis') return button;
        if (selector === '#external-analysis') return input;
        if (selector === '#status') return status;
        return null;
      },
    },
  };
}

{
  const imported = resultWithQuestions([frontQuestion]);
  const dom = fakeImportDom(JSON.stringify(imported));
  const eventTarget = new EventTarget();
  let rerenders = 0;
  eventTarget.addEventListener('boldungo:analysis-result-v1-imported', () => {
    rerenders += 1;
  });

  installSophieR001ResultImport({
    documentObject: dom.documentObject,
    eventTarget,
    importResult: async () => ({
      project_id: 'PROJECT_A',
      package_id: imported.package_id,
      imported_at: '2026-10-02T10:30:00Z',
    }),
  });

  await dom.button.listener({
    preventDefault() {},
    stopImmediatePropagation() {},
  });

  assert.equal(rerenders, 1);
  assert.equal(dom.status.textContent, 'Résultat Sophie R001 validé.');
}

console.log('BOLDUNGO-082B7 Sophie R001 photo/question view contract passed');
