const SCHEMA_VERSION = 'boldungo.exchange.v1';
const PACKAGE_ID_RE = /^PKG_[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;
const ROUND_ID_RE = /^R\d{3,}$/;
const OBSERVATION_ID_RE = /^O\d{3,}$/;
const HUMAN_FACT_ID_RE = /^HF\d{3,}$/;
const ENTITY_ID_RE = /^E\d{3,}$/;
const RELATION_ID_RE = /^R\d{3,}$/;
const UNCERTAINTY_ID_RE = /^U\d{3,}$/;
const QUESTION_ID_RE = /^Q\d{3,}$/;
const PHOTO_ID_RE = /^(FRONT|RIGHT|LEFT|REAR)_\d{3,}$/;

const ENTITY_TYPES = new Set([
  'VOLUME',
  'SURFACE',
  'OPENING',
  'ASSEMBLY',
  'SITE_ELEMENT',
  'OTHER_PHYSICAL',
]);

const RELATION_TYPES = new Set([
  'PART_OF',
  'CONNECTED_TO',
  'ABOVE',
  'LEFT_OF',
  'IN_FRONT_OF',
  'ALIGNED_WITH',
  'SAME_LEVEL_AS',
  'CONTINUOUS_WITH',
]);

const SYMMETRIC_RELATION_TYPES = new Set([
  'CONNECTED_TO',
  'ALIGNED_WITH',
  'SAME_LEVEL_AS',
  'CONTINUOUS_WITH',
]);

const UNCERTAINTY_TYPES = new Set([
  'AMBIGUOUS',
  'PARTIALLY_OBSERVABLE',
  'NOT_OBSERVABLE',
]);

const RESOLUTION_STATES = new Set(['OPEN', 'RESOLVED']);
const QUESTION_SCOPES = new Set(['PHOTO', 'GLOBAL']);
const ANSWER_TYPES = new Set(['YES_NO', 'SINGLE_CHOICE', 'FREE_TEXT']);


class AnalysisResultValidationError extends Error {}


function fail(message) {
  throw new AnalysisResultValidationError(message);
}


function isObject(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}


function exactObject(value, keys, label) {
  if (!isObject(value)) fail(`${label} doit être un objet`);
  const actual = Object.keys(value);
  for (const key of keys) {
    if (!Object.prototype.hasOwnProperty.call(value, key)) {
      fail(`${label}.${key} manquant`);
    }
  }
  const extras = actual.filter(key => !keys.includes(key));
  if (extras.length) {
    fail(`${label} contient un champ supplémentaire interdit: ${extras[0]}`);
  }
}


function nonEmptyString(value, label) {
  if (typeof value !== 'string' || !value.trim()) {
    fail(`${label} doit être une chaîne non vide`);
  }
  return value;
}


function id(value, pattern, label) {
  nonEmptyString(value, label);
  if (!pattern.test(value)) fail(`${label} invalide: ${value}`);
  return value;
}


function enumValue(value, allowed, label) {
  if (!allowed.has(value)) fail(`${label} invalide: ${String(value)}`);
  return value;
}


function array(value, label) {
  if (!Array.isArray(value)) fail(`${label} doit être une liste`);
  return value;
}


function uniqueStrings(values, label) {
  const seen = new Set();
  for (const value of values) {
    if (seen.has(value)) fail(`${label} contient un identifiant dupliqué: ${value}`);
    seen.add(value);
  }
}


function refs(value, pattern, label, { min = 0 } = {}) {
  array(value, label);
  if (value.length < min) fail(`${label} doit contenir au moins ${min} référence(s)`);
  for (const item of value) id(item, pattern, label);
  uniqueStrings(value, label);
  return value;
}


function packageId(value, label = 'package_id') {
  nonEmptyString(value, label);
  if (!PACKAGE_ID_RE.test(value)) fail(`${label} invalide`);
  return value;
}


function createdAt(value) {
  nonEmptyString(value, 'created_at');
  if (!/^\d{4}-\d{2}-\d{2}T.+(?:Z|\+00:00)$/.test(value) || Number.isNaN(Date.parse(value))) {
    fail('created_at doit être une date ISO 8601 UTC');
  }
}


function validateObservation(value, index) {
  const label = `payload.analysis.observations[${index}]`;
  exactObject(value, ['observation_id', 'photo_id', 'region_hint', 'observation_text'], label);
  id(value.observation_id, OBSERVATION_ID_RE, `${label}.observation_id`);
  id(value.photo_id, PHOTO_ID_RE, `${label}.photo_id`);
  nonEmptyString(value.region_hint, `${label}.region_hint`);
  nonEmptyString(value.observation_text, `${label}.observation_text`);
}


function validateHumanFact(value, index) {
  const label = `payload.analysis.human_facts[${index}]`;
  exactObject(
    value,
    ['human_fact_id', 'source_round_id', 'source_question_id', 'source_package_id', 'fact_text'],
    label,
  );
  id(value.human_fact_id, HUMAN_FACT_ID_RE, `${label}.human_fact_id`);
  id(value.source_round_id, ROUND_ID_RE, `${label}.source_round_id`);
  id(value.source_question_id, QUESTION_ID_RE, `${label}.source_question_id`);
  packageId(value.source_package_id, `${label}.source_package_id`);
  nonEmptyString(value.fact_text, `${label}.fact_text`);
}


function validateEntity(value, index) {
  const label = `payload.analysis.entities[${index}]`;
  exactObject(value, ['entity_id', 'entity_type', 'description', 'observation_refs'], label);
  id(value.entity_id, ENTITY_ID_RE, `${label}.entity_id`);
  enumValue(value.entity_type, ENTITY_TYPES, `${label}.entity_type`);
  nonEmptyString(value.description, `${label}.description`);
  refs(value.observation_refs, OBSERVATION_ID_RE, `${label}.observation_refs`, { min: 1 });
}


function validateRelation(value, index) {
  const label = `payload.analysis.relations[${index}]`;
  exactObject(
    value,
    ['relation_id', 'relation_type', 'subject_entity_id', 'object_entity_id', 'observation_refs'],
    label,
  );
  id(value.relation_id, RELATION_ID_RE, `${label}.relation_id`);
  enumValue(value.relation_type, RELATION_TYPES, `${label}.relation_type`);
  id(value.subject_entity_id, ENTITY_ID_RE, `${label}.subject_entity_id`);
  id(value.object_entity_id, ENTITY_ID_RE, `${label}.object_entity_id`);
  if (value.subject_entity_id === value.object_entity_id) {
    fail(`${label} doit relier deux entities distinctes`);
  }
  refs(value.observation_refs, OBSERVATION_ID_RE, `${label}.observation_refs`, { min: 1 });
}


function validateUncertainty(value, index) {
  const label = `payload.analysis.uncertainties[${index}]`;
  exactObject(
    value,
    [
      'uncertainty_id',
      'uncertainty_type',
      'description',
      'observation_refs',
      'entity_refs',
      'relation_refs',
      'resolution_state',
      'resolved_by_human_fact_refs',
      'resolved_by_observation_refs',
    ],
    label,
  );
  id(value.uncertainty_id, UNCERTAINTY_ID_RE, `${label}.uncertainty_id`);
  enumValue(value.uncertainty_type, UNCERTAINTY_TYPES, `${label}.uncertainty_type`);
  nonEmptyString(value.description, `${label}.description`);
  refs(value.observation_refs, OBSERVATION_ID_RE, `${label}.observation_refs`);
  refs(value.entity_refs, ENTITY_ID_RE, `${label}.entity_refs`);
  refs(value.relation_refs, RELATION_ID_RE, `${label}.relation_refs`);
  enumValue(value.resolution_state, RESOLUTION_STATES, `${label}.resolution_state`);
  refs(
    value.resolved_by_human_fact_refs,
    HUMAN_FACT_ID_RE,
    `${label}.resolved_by_human_fact_refs`,
  );
  refs(
    value.resolved_by_observation_refs,
    OBSERVATION_ID_RE,
    `${label}.resolved_by_observation_refs`,
  );

  if (!(value.observation_refs.length || value.entity_refs.length || value.relation_refs.length)) {
    fail(`${label} doit référencer au moins une observation, entity ou relation historique`);
  }

  if (value.resolution_state === 'OPEN') {
    if (value.resolved_by_human_fact_refs.length || value.resolved_by_observation_refs.length) {
      fail(`${label} OPEN ne peut contenir aucune référence de résolution`);
    }
  } else if (!(value.resolved_by_human_fact_refs.length || value.resolved_by_observation_refs.length)) {
    fail(`${label} RESOLVED exige au moins une référence de résolution`);
  }

  const historicalObservations = new Set(value.observation_refs);
  for (const observationId of value.resolved_by_observation_refs) {
    if (historicalObservations.has(observationId)) {
      fail(`${label} ne peut utiliser la même observation comme preuve historique et preuve de résolution`);
    }
  }
}


function validateChoice(value, questionLabel, index) {
  const label = `${questionLabel}.choices[${index}]`;
  exactObject(value, ['value', 'label'], label);
  nonEmptyString(value.value, `${label}.value`);
  if (!/^[\x00-\x7F]+$/.test(value.value)) {
    fail(`${label}.value doit être ASCII`);
  }
  nonEmptyString(value.label, `${label}.label`);
}


function validateQuestion(value, index) {
  const label = `payload.questions[${index}]`;
  exactObject(
    value,
    [
      'question_id',
      'scope',
      'photo_refs',
      'subject_hint',
      'question_text',
      'answer_type',
      'choices',
      'allow_unknown',
      'uncertainty_refs',
    ],
    label,
  );

  id(value.question_id, QUESTION_ID_RE, `${label}.question_id`);
  enumValue(value.scope, QUESTION_SCOPES, `${label}.scope`);
  refs(value.photo_refs, PHOTO_ID_RE, `${label}.photo_refs`);
  nonEmptyString(value.question_text, `${label}.question_text`);
  enumValue(value.answer_type, ANSWER_TYPES, `${label}.answer_type`);
  if (typeof value.allow_unknown !== 'boolean') {
    fail(`${label}.allow_unknown doit être booléen`);
  }
  refs(value.uncertainty_refs, UNCERTAINTY_ID_RE, `${label}.uncertainty_refs`, { min: 1 });

  if (value.scope === 'PHOTO') {
    if (!value.photo_refs.length) fail(`${label} PHOTO exige au moins un photo_ref`);
    nonEmptyString(value.subject_hint, `${label}.subject_hint`);
  } else {
    if (value.photo_refs.length) fail(`${label} GLOBAL exige photo_refs=[]`);
    if (value.subject_hint !== null) fail(`${label} GLOBAL exige subject_hint=null`);
  }

  array(value.choices, `${label}.choices`);
  value.choices.forEach((choice, choiceIndex) => validateChoice(choice, label, choiceIndex));
  if (value.answer_type === 'SINGLE_CHOICE') {
    if (value.choices.length < 2) fail(`${label} SINGLE_CHOICE exige au moins deux choix`);
    uniqueStrings(value.choices.map(choice => choice.value), `${label}.choices.value`);
  } else if (value.choices.length) {
    fail(`${label}.choices doit être vide hors SINGLE_CHOICE`);
  }
}


function uniqueIds(items, field, label) {
  uniqueStrings(items.map(item => item[field]), label);
}


function validateInternalReferences(analysis, questions) {
  const observationIds = new Set(analysis.observations.map(item => item.observation_id));
  const humanFactIds = new Set(analysis.human_facts.map(item => item.human_fact_id));
  const entityIds = new Set(analysis.entities.map(item => item.entity_id));
  const relationIds = new Set(analysis.relations.map(item => item.relation_id));
  const uncertaintyIds = new Set(analysis.uncertainties.map(item => item.uncertainty_id));

  for (const entity of analysis.entities) {
    for (const observationId of entity.observation_refs) {
      if (!observationIds.has(observationId)) {
        fail(`entity ${entity.entity_id} référence une observation inconnue: ${observationId}`);
      }
    }
  }

  const symmetricSeen = new Set();
  for (const relation of analysis.relations) {
    if (!entityIds.has(relation.subject_entity_id) || !entityIds.has(relation.object_entity_id)) {
      fail(`relation ${relation.relation_id} référence une entity inconnue`);
    }
    for (const observationId of relation.observation_refs) {
      if (!observationIds.has(observationId)) {
        fail(`relation ${relation.relation_id} référence une observation inconnue: ${observationId}`);
      }
    }
    if (SYMMETRIC_RELATION_TYPES.has(relation.relation_type)) {
      const pair = [relation.subject_entity_id, relation.object_entity_id].sort().join('|');
      const key = `${relation.relation_type}|${pair}`;
      if (symmetricSeen.has(key)) {
        fail(`relation symétrique dupliquée: ${relation.relation_type} ${pair}`);
      }
      symmetricSeen.add(key);
    }
  }

  for (const uncertainty of analysis.uncertainties) {
    for (const observationId of uncertainty.observation_refs) {
      if (!observationIds.has(observationId)) {
        fail(`uncertainty ${uncertainty.uncertainty_id} référence une observation inconnue: ${observationId}`);
      }
    }
    for (const entityId of uncertainty.entity_refs) {
      if (!entityIds.has(entityId)) {
        fail(`uncertainty ${uncertainty.uncertainty_id} référence une entity inconnue: ${entityId}`);
      }
    }
    for (const relationId of uncertainty.relation_refs) {
      if (!relationIds.has(relationId)) {
        fail(`uncertainty ${uncertainty.uncertainty_id} référence une relation inconnue: ${relationId}`);
      }
    }
    for (const humanFactId of uncertainty.resolved_by_human_fact_refs) {
      if (!humanFactIds.has(humanFactId)) {
        fail(`uncertainty ${uncertainty.uncertainty_id} référence un human_fact inconnu: ${humanFactId}`);
      }
    }
    for (const observationId of uncertainty.resolved_by_observation_refs) {
      if (!observationIds.has(observationId)) {
        fail(`uncertainty ${uncertainty.uncertainty_id} référence une observation de résolution inconnue: ${observationId}`);
      }
    }
  }

  for (const question of questions) {
    for (const uncertaintyId of question.uncertainty_refs) {
      if (!uncertaintyIds.has(uncertaintyId)) {
        fail(`question ${question.question_id} référence une uncertainty inconnue: ${uncertaintyId}`);
      }
    }
  }
}


function assertAnalysisResultV1(document) {
  exactObject(
    document,
    [
      'schema_version',
      'message_type',
      'project_id',
      'agent_id',
      'agent_display_name',
      'round_id',
      'package_id',
      'created_at',
      'payload',
    ],
    'document',
  );

  if (document.schema_version !== SCHEMA_VERSION) {
    fail(`schema_version invalide: ${String(document.schema_version)}`);
  }
  if (document.message_type !== 'ANALYSIS_RESULT') {
    fail(`message_type invalide: attendu ANALYSIS_RESULT, reçu ${String(document.message_type)}`);
  }
  nonEmptyString(document.project_id, 'project_id');
  nonEmptyString(document.agent_id, 'agent_id');
  nonEmptyString(document.agent_display_name, 'agent_display_name');
  id(document.round_id, ROUND_ID_RE, 'round_id');
  packageId(document.package_id);
  createdAt(document.created_at);

  exactObject(document.payload, ['analysis', 'questions'], 'payload');
  exactObject(
    document.payload.analysis,
    ['observations', 'human_facts', 'entities', 'relations', 'uncertainties'],
    'payload.analysis',
  );

  const analysis = document.payload.analysis;
  array(analysis.observations, 'payload.analysis.observations');
  array(analysis.human_facts, 'payload.analysis.human_facts');
  array(analysis.entities, 'payload.analysis.entities');
  array(analysis.relations, 'payload.analysis.relations');
  array(analysis.uncertainties, 'payload.analysis.uncertainties');
  array(document.payload.questions, 'payload.questions');

  analysis.observations.forEach(validateObservation);
  analysis.human_facts.forEach(validateHumanFact);
  analysis.entities.forEach(validateEntity);
  analysis.relations.forEach(validateRelation);
  analysis.uncertainties.forEach(validateUncertainty);
  document.payload.questions.forEach(validateQuestion);

  uniqueIds(analysis.observations, 'observation_id', 'observation_id');
  uniqueIds(analysis.human_facts, 'human_fact_id', 'human_fact_id');
  uniqueIds(analysis.entities, 'entity_id', 'entity_id');
  uniqueIds(analysis.relations, 'relation_id', 'relation_id');
  uniqueIds(analysis.uncertainties, 'uncertainty_id', 'uncertainty_id');
  uniqueIds(document.payload.questions, 'question_id', 'question_id');

  validateInternalReferences(analysis, document.payload.questions);
}


export function isBoldungoExchangeV1(document) {
  return isObject(document) && document.schema_version === SCHEMA_VERSION;
}


export function validateAnalysisResultV1(document) {
  try {
    assertAnalysisResultV1(document);
    return { valid: true, reason: null };
  } catch (error) {
    return {
      valid: false,
      reason: error instanceof Error ? error.message : String(error),
    };
  }
}
