import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

import {
  isBoldungoExchangeV1,
  validateAnalysisResultV1,
} from '../frontend/analysis-result-validator-v1.js';
import {
  importSophieR001AnalysisResult,
  installSophieR001ResultImport,
  validateSophieR001ResultForProject,
} from '../frontend/analysis-result-import-v1.js';
import {
  appendAnalysisResultImportToProjectRecord,
} from '../frontend/project-photo-store.js';


const fixture = JSON.parse(await readFile(
  new URL('./fixtures/exchange_v1/analysis_result_valid.json', import.meta.url),
  'utf8',
));

function clone(value) {
  return structuredClone(value);
}

function projectFor(document = fixture) {
  return {
    project_id: document.project_id,
    analysis_package_exports: [
      {
        agent_id: 'SOPHIE',
        agent_display_name: 'Sophie',
        round_id: 'R001',
        package_id: document.package_id,
        filename: 'BOLDUNGO_PROJECT_A_SOPHIE_R001.zip',
        created_at: '2026-10-01T11:30:00Z',
      },
    ],
    analysis_result_imports: [],
  };
}

{
  const result = validateAnalysisResultV1(fixture);
  assert.deepEqual(result, { valid: true, reason: null });
  assert.equal(isBoldungoExchangeV1(fixture), true);
}

{
  const invalid = clone(fixture);
  invalid.payload.analysis.relations[0].relation_type = 'NEAR';
  const result = validateAnalysisResultV1(invalid);
  assert.equal(result.valid, false);
  assert.match(result.reason, /relation_type invalide/);
}

{
  const invalid = clone(fixture);
  invalid.payload.analysis.entities[0].observation_refs = ['O999'];
  const result = validateAnalysisResultV1(invalid);
  assert.equal(result.valid, false);
  assert.match(result.reason, /observation inconnue/);
}

{
  const invalid = clone(fixture);
  invalid.payload.analysis.uncertainties[0].resolution_state = 'RESOLVED';
  const result = validateAnalysisResultV1(invalid);
  assert.equal(result.valid, false);
  assert.match(result.reason, /RESOLVED exige/);
}

{
  const invalid = clone(fixture);
  invalid.payload.questions[0].uncertainty_refs = ['U999'];
  const result = validateAnalysisResultV1(invalid);
  assert.equal(result.valid, false);
  assert.match(result.reason, /uncertainty inconnue/);
}

{
  const invalid = clone(fixture);
  invalid.payload.analysis.observations[0].confidence = 0.9;
  const result = validateAnalysisResultV1(invalid);
  assert.equal(result.valid, false);
  assert.match(result.reason, /champ supplémentaire interdit/);
}

{
  const invalid = clone(fixture);
  invalid.payload.analysis.relations = [
    {
      relation_id: 'R001',
      relation_type: 'CONNECTED_TO',
      subject_entity_id: 'E001',
      object_entity_id: 'E002',
      observation_refs: ['O001', 'O002'],
    },
    {
      relation_id: 'R002',
      relation_type: 'CONNECTED_TO',
      subject_entity_id: 'E002',
      object_entity_id: 'E001',
      observation_refs: ['O001', 'O002'],
    },
  ];
  const result = validateAnalysisResultV1(invalid);
  assert.equal(result.valid, false);
  assert.match(result.reason, /relation symétrique dupliquée/);
}

{
  const result = validateSophieR001ResultForProject(fixture, projectFor());
  assert.deepEqual(result, { valid: true, reason: null });
}

{
  const unknownPackage = clone(fixture);
  unknownPackage.package_id = 'PKG_6ba7b810-9dad-41d1-80b4-00c04fd430c8';
  const result = validateSophieR001ResultForProject(unknownPackage, projectFor());
  assert.equal(result.valid, false);
  assert.match(result.reason, /package_id inconnu/);
}

{
  const wrongProject = clone(fixture);
  wrongProject.project_id = 'OTHER_PROJECT';
  const result = validateSophieR001ResultForProject(wrongProject, projectFor());
  assert.equal(result.valid, false);
  assert.match(result.reason, /mauvais project_id/);
}

{
  const wrongAgent = clone(fixture);
  wrongAgent.agent_id = 'OTHER_AGENT';
  const result = validateSophieR001ResultForProject(wrongAgent, projectFor());
  assert.equal(result.valid, false);
  assert.match(result.reason, /mauvais agent_id/);
}

{
  const wrongRound = clone(fixture);
  wrongRound.round_id = 'R002';
  const result = validateSophieR001ResultForProject(wrongRound, projectFor());
  assert.equal(result.valid, false);
  assert.match(result.reason, /mauvais round_id/);
}

{
  const project = projectFor();
  const exportsBefore = clone(project.analysis_package_exports);
  const persisted = appendAnalysisResultImportToProjectRecord(
    project,
    fixture,
    '2026-10-02T08:30:00Z',
  );

  assert.deepEqual(persisted.analysis_package_exports, exportsBefore);
  assert.equal(persisted.analysis_result_imports.length, 1);
  assert.equal(
    persisted.analysis_result_imports[0].imported_at,
    '2026-10-02T08:30:00Z',
  );
  assert.deepEqual(persisted.analysis_result_imports[0].document, fixture);
  assert.notStrictEqual(persisted.analysis_result_imports[0].document, fixture);
}

{
  const project = projectFor();
  const persistedCalls = [];
  const result = await importSophieR001AnalysisResult(fixture, {
    getActiveProjectFn: async () => project,
    persistResultFn: async (projectId, document, importedAt) => {
      persistedCalls.push({ projectId, document: clone(document), importedAt });
    },
    now: () => '2026-10-02T08:45:00Z',
  });

  assert.deepEqual(result, {
    project_id: 'PROJECT_A',
    package_id: fixture.package_id,
    imported_at: '2026-10-02T08:45:00Z',
  });
  assert.equal(persistedCalls.length, 1);
  assert.equal(persistedCalls[0].projectId, 'PROJECT_A');
  assert.deepEqual(persistedCalls[0].document, fixture);
}

function fakeImportDom(raw) {
  const status = { textContent: '' };
  const input = { value: raw };
  const button = {
    disabled: false,
    listener: null,
    options: null,
    addEventListener(type, listener, options) {
      assert.equal(type, 'click');
      this.listener = listener;
      this.options = options;
    },
  };
  return {
    button,
    input,
    status,
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
  const dom = fakeImportDom(JSON.stringify(fixture));
  let importCalls = 0;
  installSophieR001ResultImport({
    documentObject: dom.documentObject,
    importResult: async document => {
      importCalls += 1;
      assert.deepEqual(document, fixture);
    },
  });

  const eventCalls = [];
  await dom.button.listener({
    preventDefault: () => eventCalls.push('preventDefault'),
    stopImmediatePropagation: () => eventCalls.push('stopImmediatePropagation'),
  });

  assert.equal(dom.button.options.capture, true);
  assert.deepEqual(eventCalls, ['preventDefault', 'stopImmediatePropagation']);
  assert.equal(importCalls, 1);
  assert.equal(dom.status.textContent, 'Résultat Sophie R001 validé.');
  assert.equal(dom.button.disabled, false);
}

{
  const legacy = { schema_version: '0.1', id: 'legacy-survey' };
  const dom = fakeImportDom(JSON.stringify(legacy));
  let importCalls = 0;
  installSophieR001ResultImport({
    documentObject: dom.documentObject,
    importResult: async () => { importCalls += 1; },
  });

  const eventCalls = [];
  await dom.button.listener({
    preventDefault: () => eventCalls.push('preventDefault'),
    stopImmediatePropagation: () => eventCalls.push('stopImmediatePropagation'),
  });

  assert.deepEqual(eventCalls, []);
  assert.equal(importCalls, 0);
  assert.equal(dom.status.textContent, '');
}

console.log('BOLDUNGO-082B6 Sophie R001 RESULT import contract passed');
