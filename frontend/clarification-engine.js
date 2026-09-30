export const QUESTION_TYPES = ['YES_NO', 'SINGLE_CHOICE', 'HUMAN_FACT_TEXT'];
export const GEOMETRY_IMPACTS = ['HIGH', 'MEDIUM', 'LOW', 'NONE'];
export const PRIORITIES = [
  'TARGET_BOUNDARY',
  'OBJECT_OWNERSHIP',
  'TOPOLOGY',
  'SOLID_VOID',
  'ACCESS',
  'LEVEL_CONTINUITY',
  'MATERIAL',
  'DETAIL',
];
export const EVIDENCE_STATES = ['RECOVERED', 'PARTIAL', 'NOT_OBSERVABLE'];
export const ANSWER_STATES = [
  'OPEN',
  'RESOLVED',
  'UNKNOWN',
  'PHOTO_REQUESTED',
  'NOT_APPLICABLE',
  'CONFLICT',
];
export const PROVENANCES = [
  'PHOTO_RECOVERED',
  'PHOTO_PARTIAL',
  'HUMAN_FACT',
  'REQUESTED_PHOTO_RECOVERED',
  'CONTEXTUAL_PRIOR',
  'UNKNOWN',
];
export const BLOCKING_STATUSES = ['BLOCKS_GEOMETRY', 'NON_BLOCKING'];
export const DEFER_POLICIES = ['ALLOWED', 'FORBIDDEN'];
export const UNKNOWN_STRATEGIES = ['DEFER_AFFECTED_GEOMETRY'];

const PRIORITY_INDEX = new Map(PRIORITIES.map((value, index) => [value, index]));

function copy(value) {
  return globalThis.structuredClone ? globalThis.structuredClone(value) : JSON.parse(JSON.stringify(value));
}

function assertEnum(value, allowed, label) {
  if (!allowed.includes(value)) throw new Error(`${label} invalide: ${value}`);
}

function choiceValues(item) {
  return (item.choices || []).map(choice => typeof choice === 'string' ? choice : choice.value);
}

function assertAnswerAllowed(item, answer) {
  if (item.question_type === 'HUMAN_FACT_TEXT') {
    if (!String(answer ?? '').trim()) throw new Error('Réponse texte requise');
    return;
  }
  if (!choiceValues(item).includes(answer)) {
    throw new Error(`Réponse invalide pour ${item.clarification_id}`);
  }
}

function validateRequestedPhotoSpec(spec) {
  if (!spec) return;
  for (const key of [
    'target_subject',
    'purpose',
    'camera_position_hint',
    'what_must_be_visible',
    'question_ids_expected_to_resolve',
  ]) {
    if (spec[key] == null || spec[key] === '') throw new Error(`RequestedPhotoSpec incomplet: ${key}`);
  }
  if (!Array.isArray(spec.question_ids_expected_to_resolve) || !spec.question_ids_expected_to_resolve.length) {
    throw new Error('RequestedPhotoSpec.question_ids_expected_to_resolve requis');
  }
}

export function validateClarificationItem(item) {
  if (!item || typeof item !== 'object') throw new Error('ClarificationItem requis');
  for (const key of [
    'clarification_id',
    'subject',
    'question_text',
    'question_type',
    'geometry_impact',
    'priority',
    'depends_on',
    'evidence_state',
    'answer_state',
    'provenance',
    'blocking_status',
    'defer_policy',
    'created_at',
  ]) {
    if (item[key] == null) throw new Error(`ClarificationItem.${key} requis`);
  }
  for (const key of ['subject_id', 'subject_kind', 'attribute']) {
    if (!item.subject?.[key]) throw new Error(`ClarificationItem.subject.${key} requis`);
  }
  assertEnum(item.question_type, QUESTION_TYPES, 'question_type');
  assertEnum(item.geometry_impact, GEOMETRY_IMPACTS, 'geometry_impact');
  assertEnum(item.priority, PRIORITIES, 'priority');
  assertEnum(item.evidence_state, EVIDENCE_STATES, 'evidence_state');
  assertEnum(item.answer_state, ANSWER_STATES, 'answer_state');
  assertEnum(item.provenance, PROVENANCES, 'provenance');
  assertEnum(item.blocking_status, BLOCKING_STATUSES, 'blocking_status');
  assertEnum(item.defer_policy, DEFER_POLICIES, 'defer_policy');

  if (!Array.isArray(item.depends_on)) throw new Error('depends_on doit être une liste');
  for (const dependency of item.depends_on) {
    if (!dependency.parent_clarification_id) throw new Error('parent_clarification_id requis');
    if (dependency.operator !== 'ANSWER_IN') throw new Error('Seul ANSWER_IN est supporté en v1');
    if (!Array.isArray(dependency.values) || !dependency.values.length) throw new Error('dependency.values requis');
  }

  const choices = item.choices || [];
  if (item.question_type !== 'HUMAN_FACT_TEXT' && !choices.length) {
    throw new Error(`choices requis pour ${item.question_type}`);
  }
  validateRequestedPhotoSpec(item.requested_photo_spec);

  if (item.answer_state === 'RESOLVED' && item.answer == null) {
    throw new Error('answer requis quand answer_state=RESOLVED');
  }
  if (item.answer_state === 'PHOTO_REQUESTED' && !item.requested_photo_spec) {
    throw new Error('requested_photo_spec requis quand answer_state=PHOTO_REQUESTED');
  }
  return item;
}

export function normalizeClarifications(items) {
  if (!Array.isArray(items)) throw new Error('clarifications doit être une liste');
  const ids = new Set();
  return items.map((raw, index) => {
    const item = copy(raw);
    item.choices = item.choices || [];
    item.depends_on = item.depends_on || [];
    item.answer = item.answer ?? null;
    item.answer_note = item.answer_note ?? null;
    item.requested_photo_spec = item.requested_photo_spec ?? null;
    item.unknown_strategy = item.unknown_strategy ?? null;
    item.answered_at = item.answered_at ?? null;
    item.conflict = item.conflict ?? null;
    item.conflict_resolution = item.conflict_resolution ?? null;
    item.catalog_order = Number.isFinite(item.catalog_order) ? item.catalog_order : index;
    validateClarificationItem(item);
    if (ids.has(item.clarification_id)) throw new Error(`clarification_id dupliqué: ${item.clarification_id}`);
    ids.add(item.clarification_id);
    return item;
  });
}

function dependencyStatus(item, byId) {
  if (!item.depends_on.length) return 'SATISFIED';
  let unresolved = false;
  for (const dependency of item.depends_on) {
    const parent = byId.get(dependency.parent_clarification_id);
    if (!parent) throw new Error(`Parent introuvable: ${dependency.parent_clarification_id}`);
    if (parent.answer_state !== 'RESOLVED') {
      unresolved = true;
      continue;
    }
    if (!dependency.values.includes(parent.answer)) return 'NOT_APPLICABLE';
  }
  return unresolved ? 'WAITING' : 'SATISFIED';
}

export function recomputeDependencies(items) {
  const next = normalizeClarifications(items);
  const byId = new Map(next.map(item => [item.clarification_id, item]));
  for (const item of next) {
    if (!item.depends_on.length) continue;
    const status = dependencyStatus(item, byId);
    if (status === 'NOT_APPLICABLE') {
      item.answer_state = 'NOT_APPLICABLE';
      item.answer = null;
      item.answer_note = null;
      item.provenance = 'UNKNOWN';
      item.unknown_strategy = null;
      item.answered_at = null;
    } else if (status === 'SATISFIED' && item.answer_state === 'NOT_APPLICABLE') {
      item.answer_state = 'OPEN';
      item.provenance = item.evidence_state === 'RECOVERED' ? 'PHOTO_RECOVERED'
        : item.evidence_state === 'PARTIAL' ? 'PHOTO_PARTIAL' : 'UNKNOWN';
    }
  }
  return next;
}

export function isItemActive(item, items) {
  const normalized = recomputeDependencies(items);
  const byId = new Map(normalized.map(candidate => [candidate.clarification_id, candidate]));
  const target = byId.get(item.clarification_id);
  if (!target || target.answer_state === 'NOT_APPLICABLE') return false;
  return dependencyStatus(target, byId) === 'SATISFIED';
}

export function activeQuestionQueue(items) {
  const next = recomputeDependencies(items);
  const byId = new Map(next.map(item => [item.clarification_id, item]));
  return next
    .filter(item => item.answer_state === 'OPEN' && dependencyStatus(item, byId) === 'SATISFIED')
    .sort((a, b) => (
      PRIORITY_INDEX.get(a.priority) - PRIORITY_INDEX.get(b.priority)
      || a.catalog_order - b.catalog_order
      || a.clarification_id.localeCompare(b.clarification_id)
    ));
}

function factIdFor(clarificationId) {
  return `HUMAN_${clarificationId}`;
}

export function upsertHumanFact(humanFacts, item, value, timestamp = new Date().toISOString()) {
  const facts = Array.isArray(humanFacts) ? copy(humanFacts) : [];
  const index = facts.findIndex(fact => fact.clarification_id === item.clarification_id);
  const previous = index >= 0 ? facts[index] : null;
  const fact = {
    fact_id: previous?.fact_id || factIdFor(item.clarification_id),
    clarification_id: item.clarification_id,
    subject: copy(item.subject),
    value,
    created_at: previous?.created_at || timestamp,
    updated_at: timestamp,
    source: 'HUMAN',
  };
  if (index >= 0) facts[index] = fact;
  else facts.push(fact);
  return facts;
}

function conflictFor(item, humanAnswer) {
  if (item.evidence_state !== 'RECOVERED' || item.evidence_answer == null) return null;
  if (item.evidence_answer === humanAnswer) return null;
  return {
    photo: { value: item.evidence_answer, provenance: 'PHOTO_RECOVERED' },
    human: { value: humanAnswer, provenance: 'HUMAN_FACT' },
  };
}

export function applyHumanAnswer(items, humanFacts, clarificationId, answer, {
  answerNote = null,
  timestamp = new Date().toISOString(),
} = {}) {
  const next = normalizeClarifications(items);
  const item = next.find(candidate => candidate.clarification_id === clarificationId);
  if (!item) throw new Error(`Clarification introuvable: ${clarificationId}`);
  assertAnswerAllowed(item, answer);

  const conflict = conflictFor(item, answer);
  item.answer = answer;
  item.answer_note = answerNote;
  item.answered_at = timestamp;
  item.unknown_strategy = null;
  item.conflict_resolution = null;
  item.provenance = 'HUMAN_FACT';
  if (conflict) {
    item.answer_state = 'CONFLICT';
    item.conflict = conflict;
  } else {
    item.answer_state = 'RESOLVED';
    item.conflict = null;
  }

  const facts = upsertHumanFact(humanFacts, item, answer, timestamp);
  return { clarifications: recomputeDependencies(next), human_facts: facts };
}

export function applyPreexistingHumanFacts(items, humanFacts) {
  let clarifications = normalizeClarifications(items);
  const facts = Array.isArray(humanFacts) ? copy(humanFacts) : [];
  for (const fact of facts) {
    const item = clarifications.find(candidate => candidate.clarification_id === fact.clarification_id);
    if (!item) continue;
    const conflict = conflictFor(item, fact.value);
    item.answer = fact.value;
    item.answered_at = fact.updated_at || fact.created_at || new Date().toISOString();
    item.provenance = 'HUMAN_FACT';
    item.unknown_strategy = null;
    item.conflict_resolution = null;
    if (conflict) {
      item.answer_state = 'CONFLICT';
      item.conflict = conflict;
    } else {
      item.answer_state = 'RESOLVED';
      item.conflict = null;
    }
    clarifications = recomputeDependencies(clarifications);
  }
  return { clarifications, human_facts: facts };
}

export function markUnknown(items, clarificationId, {
  unknownStrategy = null,
  timestamp = new Date().toISOString(),
} = {}) {
  const next = normalizeClarifications(items);
  const item = next.find(candidate => candidate.clarification_id === clarificationId);
  if (!item) throw new Error(`Clarification introuvable: ${clarificationId}`);
  if (unknownStrategy != null) {
    assertEnum(unknownStrategy, UNKNOWN_STRATEGIES, 'unknown_strategy');
    if (item.defer_policy !== 'ALLOWED') throw new Error('Déférence interdite pour cette clarification');
  }
  item.answer_state = 'UNKNOWN';
  item.answer = null;
  item.answer_note = null;
  item.provenance = 'UNKNOWN';
  item.unknown_strategy = unknownStrategy;
  item.answered_at = timestamp;
  item.conflict = null;
  item.conflict_resolution = null;
  return recomputeDependencies(next);
}

export function setUnknownStrategy(items, clarificationId, strategy) {
  assertEnum(strategy, UNKNOWN_STRATEGIES, 'unknown_strategy');
  const next = normalizeClarifications(items);
  const item = next.find(candidate => candidate.clarification_id === clarificationId);
  if (!item) throw new Error(`Clarification introuvable: ${clarificationId}`);
  if (item.answer_state !== 'UNKNOWN') throw new Error('La stratégie UNKNOWN exige answer_state=UNKNOWN');
  if (item.defer_policy !== 'ALLOWED') throw new Error('Déférence interdite pour cette clarification');
  item.unknown_strategy = strategy;
  return recomputeDependencies(next);
}

export function escalateRequestedPhoto(items, clarificationId) {
  const next = normalizeClarifications(items);
  const item = next.find(candidate => candidate.clarification_id === clarificationId);
  if (!item) throw new Error(`Clarification introuvable: ${clarificationId}`);
  if (item.answer_state !== 'UNKNOWN') throw new Error('REQUEST_PHOTO exige une réponse UNKNOWN préalable');
  if (item.blocking_status !== 'BLOCKS_GEOMETRY') throw new Error('REQUEST_PHOTO v1 réservé aux ambiguïtés géométriques bloquantes');
  if (!item.requested_photo_spec) throw new Error('Aucune photo ciblée définie pour cette clarification');
  item.answer_state = 'PHOTO_REQUESTED';
  item.provenance = 'UNKNOWN';
  item.unknown_strategy = null;
  return recomputeDependencies(next);
}

export function resolveFromRequestedPhoto(items, clarificationId, answer, {
  timestamp = new Date().toISOString(),
} = {}) {
  const next = normalizeClarifications(items);
  const item = next.find(candidate => candidate.clarification_id === clarificationId);
  if (!item) throw new Error(`Clarification introuvable: ${clarificationId}`);
  assertAnswerAllowed(item, answer);
  item.answer_state = 'RESOLVED';
  item.answer = answer;
  item.answer_note = null;
  item.provenance = 'REQUESTED_PHOTO_RECOVERED';
  item.unknown_strategy = null;
  item.answered_at = timestamp;
  item.conflict = null;
  item.conflict_resolution = null;
  return recomputeDependencies(next);
}

export function resolveConflict(items, clarificationId, action, {
  revisedAnswer = null,
  timestamp = new Date().toISOString(),
} = {}) {
  const next = normalizeClarifications(items);
  const item = next.find(candidate => candidate.clarification_id === clarificationId);
  if (!item || item.answer_state !== 'CONFLICT' || !item.conflict) {
    throw new Error('Clarification en conflit requise');
  }

  if (action === 'KEEP_HUMAN') {
    item.answer_state = 'RESOLVED';
    item.answer = item.conflict.human.value;
    item.provenance = 'HUMAN_FACT';
    item.conflict_resolution = 'HUMAN_REAFFIRMED';
    item.answered_at = timestamp;
    return recomputeDependencies(next);
  }

  if (action === 'REVISE_HUMAN') {
    assertAnswerAllowed(item, revisedAnswer);
    item.answer = revisedAnswer;
    item.conflict.human = { value: revisedAnswer, provenance: 'HUMAN_FACT' };
    item.answered_at = timestamp;
    if (item.evidence_answer === revisedAnswer) {
      item.answer_state = 'RESOLVED';
      item.provenance = 'HUMAN_FACT';
      item.conflict_resolution = 'HUMAN_REVISED';
    }
    return recomputeDependencies(next);
  }

  if (action === 'REQUEST_PHOTO') {
    if (!item.requested_photo_spec) throw new Error('Aucune photo ciblée définie');
    item.answer_state = 'PHOTO_REQUESTED';
    item.provenance = 'UNKNOWN';
    item.conflict_resolution = 'REQUESTED_PHOTO';
    return recomputeDependencies(next);
  }

  throw new Error(`Action conflit inconnue: ${action}`);
}

export function evaluateClarificationGate(items) {
  const next = recomputeDependencies(items);
  const byId = new Map(next.map(item => [item.clarification_id, item]));
  const deferred = [];
  const blocking = [];

  for (const item of next) {
    if (item.blocking_status !== 'BLOCKS_GEOMETRY') continue;
    if (item.answer_state === 'NOT_APPLICABLE') continue;
    if (dependencyStatus(item, byId) !== 'SATISFIED') continue;
    if (item.answer_state === 'RESOLVED') continue;

    if (
      item.answer_state === 'UNKNOWN'
      && item.defer_policy === 'ALLOWED'
      && item.unknown_strategy === 'DEFER_AFFECTED_GEOMETRY'
    ) {
      deferred.push(item.subject.subject_id);
      continue;
    }
    blocking.push(item.clarification_id);
  }

  const deferredSubjects = [...new Set(deferred)].sort();
  if (blocking.length) {
    return {
      gate: 'BLOCKED',
      geometry_scope: null,
      deferred_subjects: deferredSubjects,
      blocking_clarification_ids: blocking,
    };
  }
  return {
    gate: 'READY',
    geometry_scope: deferredSubjects.length ? 'PARTIAL' : 'FULL',
    deferred_subjects: deferredSubjects,
    blocking_clarification_ids: [],
  };
}
