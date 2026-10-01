import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import {
  activeQuestionQueue,
  applyHumanAnswer,
  applyPreexistingHumanFacts,
  escalateRequestedPhoto,
  evaluateClarificationGate,
  markUnknown,
  normalizeClarifications,
  resolveConflict,
} from '../frontend/clarification-engine.js';

const fixture = JSON.parse(await readFile(
  new URL('../frontend/benchmarks/real-house-5/clarifications-v1.json', import.meta.url),
  'utf8',
));

const seed = () => normalizeClarifications(fixture.clarifications);
const byId = (items, id) => items.find(item => item.clarification_id === id);

const initial = activeQuestionQueue(seed()).map(item => item.clarification_id);
assert.deepEqual(initial.slice(0, 6), [
  'A01_TARGET_BOUNDARY',
  'A02_CHIMNEY_OWNERSHIP',
  'A03_STAIR_TOPOLOGY',
  'A04_STAIR_UNDERSIDE',
  'A05_PLATFORM_UNDERSIDE',
  'A06_HIGH_ACCESS_OPENING',
]);

{
  const result = applyHumanAnswer(seed(), [], 'A06_HIGH_ACCESS_OPENING', 'WINDOW', { timestamp: '2026-01-01T00:00:00.000Z' });
  assert.equal(byId(result.clarifications, 'A07_THRESHOLD_LEVEL').answer_state, 'NOT_APPLICABLE');
  assert(!activeQuestionQueue(result.clarifications).some(item => item.clarification_id === 'A07_THRESHOLD_LEVEL'));
}

{
  const result = applyHumanAnswer(seed(), [], 'A06_HIGH_ACCESS_OPENING', 'FRENCH_DOOR', { timestamp: '2026-01-01T00:00:00.000Z' });
  assert.equal(byId(result.clarifications, 'A07_THRESHOLD_LEVEL').answer_state, 'OPEN');
  assert(activeQuestionQueue(result.clarifications).some(item => item.clarification_id === 'A07_THRESHOLD_LEVEL'));
}

{
  const facts = [{
    fact_id: 'HUMAN_A03_STAIR_TOPOLOGY',
    clarification_id: 'A03_STAIR_TOPOLOGY',
    subject: { subject_id: 'stair-exterior', subject_kind: 'STAIR', attribute: 'topology' },
    value: 'TURN_90',
    created_at: '2026-01-01T00:00:00.000Z',
    updated_at: '2026-01-01T00:00:00.000Z',
    source: 'HUMAN',
  }];
  const result = applyPreexistingHumanFacts(seed(), facts);
  const item = byId(result.clarifications, 'A03_STAIR_TOPOLOGY');
  assert.equal(item.evidence_state, 'PARTIAL');
  assert.equal(item.answer_state, 'RESOLVED');
  assert.equal(item.provenance, 'HUMAN_FACT');
  assert.equal(item.answer, 'TURN_90');
  assert(!activeQuestionQueue(result.clarifications).some(candidate => candidate.clarification_id === 'A03_STAIR_TOPOLOGY'));
}

{
  const items = markUnknown(seed(), 'A03_STAIR_TOPOLOGY', { timestamp: '2026-01-01T00:00:00.000Z' });
  const item = byId(items, 'A03_STAIR_TOPOLOGY');
  assert.equal(item.answer_state, 'UNKNOWN');
  assert.equal(item.provenance, 'UNKNOWN');
  assert.equal(item.answer, null);
  const escalated = escalateRequestedPhoto(items, 'A03_STAIR_TOPOLOGY');
  assert.equal(byId(escalated, 'A03_STAIR_TOPOLOGY').answer_state, 'PHOTO_REQUESTED');
}

{
  const result = applyHumanAnswer(seed(), [], 'A02_CHIMNEY_OWNERSHIP', 'SOME');
  const child = byId(result.clarifications, 'A02B_CHIMNEY_IDENTIFICATION');
  assert.equal(child.answer_state, 'OPEN');
  assert(activeQuestionQueue(result.clarifications).some(item => item.clarification_id === 'A02B_CHIMNEY_IDENTIFICATION'));
}

function recoveredConflictItem() {
  return normalizeClarifications([{
    clarification_id: 'C1',
    subject: { subject_id: 'wall-1', subject_kind: 'WALL', attribute: 'exists' },
    question_text: 'Le mur existe-t-il ?',
    question_type: 'YES_NO',
    choices: [{ value: 'YES', label: 'Oui' }, { value: 'NO', label: 'Non' }],
    geometry_impact: 'HIGH',
    priority: 'TARGET_BOUNDARY',
    depends_on: [],
    evidence_state: 'RECOVERED',
    evidence_answer: 'YES',
    answer_state: 'OPEN',
    provenance: 'PHOTO_RECOVERED',
    blocking_status: 'BLOCKS_GEOMETRY',
    defer_policy: 'FORBIDDEN',
    answer: null,
    answer_note: null,
    requested_photo_spec: {
      target_subject: 'wall-1',
      purpose: 'Vérifier le conflit',
      camera_position_hint: 'Face au mur',
      what_must_be_visible: 'Le mur entier',
      question_ids_expected_to_resolve: ['C1'],
    },
    unknown_strategy: null,
    created_at: '2026-01-01T00:00:00.000Z',
    answered_at: null,
  }]);
}

{
  const result = applyHumanAnswer(recoveredConflictItem(), [], 'C1', 'NO', { timestamp: '2026-01-02T00:00:00.000Z' });
  const conflict = byId(result.clarifications, 'C1');
  assert.equal(conflict.answer_state, 'CONFLICT');
  assert.equal(conflict.conflict.photo.value, 'YES');
  assert.equal(conflict.conflict.photo.provenance, 'PHOTO_RECOVERED');
  assert.equal(conflict.conflict.human.value, 'NO');
  assert.equal(conflict.conflict.human.provenance, 'HUMAN_FACT');
  assert.equal(evaluateClarificationGate(result.clarifications).gate, 'BLOCKED');

  const kept = resolveConflict(result.clarifications, 'C1', 'KEEP_HUMAN', { timestamp: '2026-01-03T00:00:00.000Z' });
  const resolved = byId(kept, 'C1');
  assert.equal(resolved.answer_state, 'RESOLVED');
  assert.equal(resolved.provenance, 'HUMAN_FACT');
  assert.equal(resolved.conflict_resolution, 'HUMAN_REAFFIRMED');
  assert.equal(resolved.evidence_answer, 'YES');
  assert.equal(resolved.conflict.photo.provenance, 'PHOTO_RECOVERED');
  assert.equal(resolved.conflict.human.provenance, 'HUMAN_FACT');
}

{
  const open = recoveredConflictItem();
  assert.equal(evaluateClarificationGate(open).gate, 'BLOCKED');

  const unknownForbidden = markUnknown(open, 'C1');
  assert.equal(evaluateClarificationGate(unknownForbidden).gate, 'BLOCKED');

  const requested = escalateRequestedPhoto(unknownForbidden, 'C1');
  assert.equal(evaluateClarificationGate(requested).gate, 'BLOCKED');
}

function deferableItem(id = 'D1', subjectId = 'stair-underside') {
  return {
    clarification_id: id,
    subject: { subject_id: subjectId, subject_kind: 'STAIR', attribute: 'underside_state' },
    question_text: 'Dessous ?',
    question_type: 'SINGLE_CHOICE',
    choices: [{ value: 'SOLID', label: 'Plein' }, { value: 'VOID', label: 'Vide' }],
    geometry_impact: 'HIGH',
    priority: 'SOLID_VOID',
    depends_on: [],
    evidence_state: 'NOT_OBSERVABLE',
    answer_state: 'OPEN',
    provenance: 'UNKNOWN',
    blocking_status: 'BLOCKS_GEOMETRY',
    defer_policy: 'ALLOWED',
    answer: null,
    answer_note: null,
    requested_photo_spec: null,
    unknown_strategy: null,
    created_at: '2026-01-01T00:00:00.000Z',
    answered_at: null,
  };
}

{
  const items = markUnknown(
    normalizeClarifications([deferableItem()]),
    'D1',
    { unknownStrategy: 'DEFER_AFFECTED_GEOMETRY' },
  );
  const gate = evaluateClarificationGate(items);
  assert.equal(gate.gate, 'READY');
  assert.equal(gate.geometry_scope, 'PARTIAL');
  assert.deepEqual(gate.deferred_subjects, ['stair-underside']);
}

{
  let items = normalizeClarifications([deferableItem('R1', 'subject-r1')]);
  const result = applyHumanAnswer(items, [], 'R1', 'SOLID');
  const gate = evaluateClarificationGate(result.clarifications);
  assert.equal(gate.gate, 'READY');
  assert.equal(gate.geometry_scope, 'FULL');
  assert.deepEqual(gate.deferred_subjects, []);
}

assert.equal(fixture.fixture_id, 'real-house-5-081');
assert.equal(fixture.clarifications.length, 10);
for (const id of [
  'A01_TARGET_BOUNDARY',
  'A02_CHIMNEY_OWNERSHIP',
  'A02B_CHIMNEY_IDENTIFICATION',
  'A03_STAIR_TOPOLOGY',
  'A04_STAIR_UNDERSIDE',
  'A05_PLATFORM_UNDERSIDE',
  'A06_HIGH_ACCESS_OPENING',
  'A07_THRESHOLD_LEVEL',
  'A08_MASONRY_TO_TIMBER_CONTINUITY',
  'A09_ROOF_MATERIAL',
]) {
  assert(byId(seed(), id), id);
}

console.log('BOLDUNGO-081C clarification engine contract passed');
