import assert from 'node:assert/strict';
import { readFile, writeFile } from 'node:fs/promises';

import {
  answerDraftsForResult,
  buildHumanAnswersV1,
  createControlsForQuestion,
  installSophieR001AnswerUi,
  makeAnswerDraft,
  syncQuestionAnswerOccurrences,
  validateAnswerDraftForQuestion,
} from '../frontend/human-answers-v1.js';
import {
  upsertAnalysisAnswerDraftToProjectRecord,
} from '../frontend/project-photo-store.js';


const sourceResult = JSON.parse(await readFile(
  new URL('./fixtures/exchange_v1/analysis_result_valid.json', import.meta.url),
  'utf8',
));

const qYesNo = sourceResult.payload.questions[0];
const qChoice = sourceResult.payload.questions[1];
const qText = sourceResult.payload.questions[2];

const yesDraft = makeAnswerDraft(sourceResult, qYesNo, 'ANSWERED', 'YES');
assert.equal(yesDraft.value, 'YES');

const noDraft = makeAnswerDraft(sourceResult, qYesNo, 'ANSWERED', 'NO');
assert.equal(noDraft.value, 'NO');

const choiceDraft = makeAnswerDraft(sourceResult, qChoice, 'ANSWERED', 'MASONRY');
assert.equal(choiceDraft.value, 'MASONRY');

const textDraft = makeAnswerDraft(
  sourceResult,
  qText,
  'ANSWERED',
  'Ancienne annexe de rangement.',
);
assert.equal(textDraft.value, 'Ancienne annexe de rangement.');

const unknownDraft = makeAnswerDraft(sourceResult, qYesNo, 'UNKNOWN', null);
assert.equal(unknownDraft.answer_state, 'UNKNOWN');
assert.equal(unknownDraft.value, null);

{
  const disallowed = structuredClone(qYesNo);
  disallowed.allow_unknown = false;
  assert.throws(
    () => makeAnswerDraft(sourceResult, disallowed, 'UNKNOWN', null),
    /n’autorise pas/,
  );
}

assert.throws(
  () => makeAnswerDraft(sourceResult, qYesNo, 'ANSWERED', 'MAYBE'),
  /YES_NO exige YES ou NO/,
);
assert.throws(
  () => makeAnswerDraft(sourceResult, qChoice, 'ANSWERED', 'STONE'),
  /choice.value déclaré/,
);
assert.throws(
  () => makeAnswerDraft(sourceResult, qText, 'ANSWERED', '   '),
  /valeur non vide/,
);

{
  const built = buildHumanAnswersV1(
    sourceResult,
    [yesDraft, textDraft],
    { createdAt: '2026-10-02T14:45:00Z' },
  );
  assert.equal(
    built.filename,
    'BOLDUNGO_PROJECT_A_SOPHIE_R001_ANSWERS.json',
  );
  assert.equal(built.document.schema_version, 'boldungo.exchange.v1');
  assert.equal(built.document.message_type, 'HUMAN_ANSWERS');
  assert.equal(built.document.project_id, sourceResult.project_id);
  assert.equal(built.document.agent_id, sourceResult.agent_id);
  assert.equal(built.document.agent_display_name, sourceResult.agent_display_name);
  assert.equal(built.document.round_id, sourceResult.round_id);
  assert.equal(built.document.package_id, sourceResult.package_id);
  assert.equal(built.document.created_at, '2026-10-02T14:45:00Z');
  assert.deepEqual(
    built.document.payload.answers.map(answer => answer.question_id),
    ['Q001', 'Q003'],
  );
  assert(built.document.payload.answers.every(answer => answer.note === null));
}

{
  const built = buildHumanAnswersV1(
    sourceResult,
    [],
    { createdAt: '2026-10-02T14:46:00Z' },
  );
  assert.deepEqual(built.document.payload.answers, []);
}

{
  assert.throws(
    () => buildHumanAnswersV1(
      sourceResult,
      [yesDraft, yesDraft],
      { createdAt: '2026-10-02T14:47:00Z' },
    ),
    /Réponse dupliquée/,
  );
}

{
  const otherPackage = {
    ...yesDraft,
    package_id: 'PKG_6ba7b810-9dad-41d1-80b4-00c04fd430c8',
  };
  const project = {
    project_id: sourceResult.project_id,
    analysis_answer_drafts: [yesDraft, otherPackage],
  };
  assert.deepEqual(answerDraftsForResult(project, sourceResult), [yesDraft]);
}

{
  const baseProject = {
    project_id: sourceResult.project_id,
    analysis_package_exports: [{ package_id: sourceResult.package_id }],
    analysis_result_imports: [{ document: sourceResult }],
    analysis_answer_drafts: [],
  };

  const once = upsertAnalysisAnswerDraftToProjectRecord(baseProject, yesDraft);
  assert.equal(once.analysis_answer_drafts.length, 1);
  assert.deepEqual(once.analysis_answer_drafts[0], yesDraft);

  const replaced = upsertAnalysisAnswerDraftToProjectRecord(once, noDraft);
  assert.equal(replaced.analysis_answer_drafts.length, 1);
  assert.deepEqual(replaced.analysis_answer_drafts[0], noDraft);

  const otherPackage = {
    ...choiceDraft,
    package_id: 'PKG_6ba7b810-9dad-41d1-80b4-00c04fd430c8',
  };
  const isolated = upsertAnalysisAnswerDraftToProjectRecord(replaced, otherPackage);
  assert.equal(isolated.analysis_answer_drafts.length, 2);
  assert.equal(answerDraftsForResult(isolated, sourceResult).length, 1);
  assert.deepEqual(answerDraftsForResult(isolated, sourceResult)[0], noDraft);
}

class FakeNode {
  constructor(tagName) {
    this.tagName = tagName;
    this.children = [];
    this.dataset = {};
    this.attributes = new Map();
    this.listeners = {};
    this.textContent = '';
    this.type = '';
    this.value = '';
    this.className = '';
    this.placeholder = '';
  }

  append(...nodes) {
    this.children.push(...nodes);
  }

  appendChild(node) {
    this.children.push(node);
    return node;
  }

  setAttribute(name, value) {
    this.attributes.set(name, String(value));
  }

  getAttribute(name) {
    return this.attributes.get(name) ?? null;
  }

  hasAttribute(name) {
    return this.attributes.has(name);
  }

  addEventListener(type, listener) {
    this.listeners[type] = listener;
  }
}

const fakeDocument = {
  createElement(tagName) {
    return new FakeNode(tagName);
  },
};

{
  const controls = createControlsForQuestion(fakeDocument, qYesNo, () => {});
  assert.deepEqual(
    controls.children.map(node => node.textContent),
    ['Oui', 'Non', 'Je ne sais pas'],
  );
  assert.equal(controls.children[0].dataset.answerValue, 'YES');
  assert.equal(controls.children[1].dataset.answerValue, 'NO');
  assert.equal(controls.children[2].dataset.answerUnknown, 'true');
}

{
  const noUnknown = structuredClone(qYesNo);
  noUnknown.allow_unknown = false;
  const controls = createControlsForQuestion(fakeDocument, noUnknown, () => {});
  assert.deepEqual(
    controls.children.map(node => node.textContent),
    ['Oui', 'Non'],
  );
}

{
  const controls = createControlsForQuestion(fakeDocument, qChoice, () => {});
  assert.deepEqual(
    controls.children.slice(0, 2).map(node => node.textContent),
    ['Maçonnerie', 'Bardage'],
  );
  assert.deepEqual(
    controls.children.slice(0, 2).map(node => node.dataset.answerValue),
    ['MASONRY', 'CLADDING'],
  );
}

{
  const controls = createControlsForQuestion(fakeDocument, qText, () => {});
  const text = controls.children.find(node => node.dataset.answerText === 'true');
  assert(text);
  assert.equal(text.type, 'text');
}

function occurrence() {
  const yes = new FakeNode('button');
  yes.dataset.answerValue = 'YES';
  yes.setAttribute('data-answer-value', 'YES');
  const no = new FakeNode('button');
  no.dataset.answerValue = 'NO';
  no.setAttribute('data-answer-value', 'NO');
  const unknown = new FakeNode('button');
  unknown.dataset.answerUnknown = 'true';
  unknown.setAttribute('data-answer-unknown', 'true');
  const text = new FakeNode('input');
  text.dataset.answerText = 'true';

  return {
    yes,
    no,
    unknown,
    text,
    querySelectorAll() {
      return [yes, no, unknown];
    },
    querySelector(selector) {
      return selector === '[data-answer-text]' ? text : null;
    },
  };
}

{
  const first = occurrence();
  const second = occurrence();
  const documentObject = {
    querySelectorAll(selector) {
      assert.equal(
        selector,
        '.sophie-v1-question[data-question-id="Q001"]',
      );
      return [first, second];
    },
  };

  syncQuestionAnswerOccurrences(documentObject, 'Q001', yesDraft);
  assert.equal(first.yes.dataset.selected, 'true');
  assert.equal(second.yes.dataset.selected, 'true');
  assert.equal(first.no.dataset.selected, 'false');
  assert.equal(second.no.dataset.selected, 'false');

  syncQuestionAnswerOccurrences(documentObject, 'Q001', unknownDraft);
  assert.equal(first.unknown.dataset.selected, 'true');
  assert.equal(second.unknown.dataset.selected, 'true');
}

{
  const eventTarget = new EventTarget();
  let refreshCount = 0;
  installSophieR001AnswerUi({
    eventTarget,
    refresh: async () => { refreshCount += 1; },
  });
  await Promise.resolve();
  const initial = refreshCount;
  eventTarget.dispatchEvent(new Event('boldungo:analysis-result-v1-rendered'));
  await Promise.resolve();
  assert.equal(refreshCount, initial + 1);
}

{
  const outputPath = process.argv[2];
  if (outputPath) {
    const built = buildHumanAnswersV1(
      sourceResult,
      [yesDraft, choiceDraft, textDraft],
      { createdAt: '2026-10-02T14:50:00Z' },
    );
    await writeFile(outputPath, JSON.stringify(built.document, null, 2));
  }
}

console.log('BOLDUNGO-082B8 HUMAN_ANSWERS contract passed');
