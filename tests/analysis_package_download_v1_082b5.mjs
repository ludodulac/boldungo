import assert from 'node:assert/strict';

import {
  SOPHIE_AGENT_DISPLAY_NAME,
  SOPHIE_AGENT_ID,
  SOPHIE_INITIAL_ROUND_ID,
  createPackageIdV1,
  downloadInitialSophiePackageV1,
  installSophieR001DownloadButton,
} from '../frontend/analysis-package-download-v1.js';
import { INITIAL_SOPHIE_PROMPT_V1 } from '../frontend/analysis-prompt-v1-initial.js';


const uuidPattern = /^PKG_[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;
const generatedA = createPackageIdV1();
const generatedB = createPackageIdV1();
assert.match(generatedA, uuidPattern);
assert.match(generatedB, uuidPattern);
assert.notEqual(generatedA, generatedB);

assert.equal(SOPHIE_AGENT_ID, 'SOPHIE');
assert.equal(SOPHIE_AGENT_DISPLAY_NAME, 'Sophie');
assert.equal(SOPHIE_INITIAL_ROUND_ID, 'R001');
assert(INITIAL_SOPHIE_PROMPT_V1.includes('boldungo.exchange.v1'));
assert(INITIAL_SOPHIE_PROMPT_V1.includes('observations'));
assert(INITIAL_SOPHIE_PROMPT_V1.includes('human_facts'));
assert(INITIAL_SOPHIE_PROMPT_V1.includes('entities'));
assert(INITIAL_SOPHIE_PROMPT_V1.includes('relations'));
assert(INITIAL_SOPHIE_PROMPT_V1.includes('uncertainties'));
assert(INITIAL_SOPHIE_PROMPT_V1.includes('Ne produis aucune géométrie LEGO'));

{
  const events = [];
  const history = [];
  const downloads = [];
  const packageIds = [
    'PKG_550e8400-e29b-41d4-a716-446655440000',
    'PKG_6ba7b810-9dad-41d1-80b4-00c04fd430c8',
  ];

  const dependencies = {
    getPackageInput: async () => {
      events.push('getActiveProjectPackageInputV1');
      return {
        project_id: 'project_house',
        photos: [{ photo_id: 'FRONT_001' }],
      };
    },
    buildPackage: async args => {
      events.push('buildAnalysisPackageZipV1');
      assert.equal(args.agent_id, 'SOPHIE');
      assert.equal(args.agent_display_name, 'Sophie');
      assert.equal(args.round_id, 'R001');
      assert.equal(args.prompt_text, INITIAL_SOPHIE_PROMPT_V1);
      assert.equal(args.package_input.project_id, 'project_house');
      return {
        filename: 'BOLDUNGO_project_house_SOPHIE_R001.zip',
        blob: new Blob(['ZIP']),
      };
    },
    persistExport: async (projectId, metadata) => {
      events.push('persistExport');
      assert.equal(projectId, 'project_house');
      history.push({ ...metadata });
    },
    packageIdFactory: () => packageIds.shift(),
    download: (blob, filename) => {
      events.push('download');
      downloads.push({ blob, filename });
    },
    now: () => '2026-10-02T08:00:00.000Z',
  };

  const first = await downloadInitialSophiePackageV1(dependencies);
  const second = await downloadInitialSophiePackageV1(dependencies);

  assert.deepEqual(events, [
    'getActiveProjectPackageInputV1',
    'buildAnalysisPackageZipV1',
    'persistExport',
    'download',
    'getActiveProjectPackageInputV1',
    'buildAnalysisPackageZipV1',
    'persistExport',
    'download',
  ]);
  assert.equal(history.length, 2);
  assert.notEqual(history[0].package_id, history[1].package_id);
  assert.equal(history[0].round_id, 'R001');
  assert.equal(history[1].round_id, 'R001');
  assert.equal(history[0].filename, 'BOLDUNGO_project_house_SOPHIE_R001.zip');
  assert.equal(history[1].filename, 'BOLDUNGO_project_house_SOPHIE_R001.zip');
  assert.equal(downloads.length, 2);
  assert.equal(downloads[0].filename, 'BOLDUNGO_project_house_SOPHIE_R001.zip');
  assert.equal(downloads[1].filename, 'BOLDUNGO_project_house_SOPHIE_R001.zip');
  assert.equal(first.package_id, history[0].package_id);
  assert.equal(second.package_id, history[1].package_id);
}

function fakeButtonDocument() {
  const status = { textContent: '' };
  const button = {
    textContent: '',
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
    status,
    documentObject: {
      querySelector(selector) {
        if (selector === '#download-ai-package') return button;
        if (selector === '#ai-package-status') return status;
        return null;
      },
    },
  };
}

{
  const fake = fakeButtonDocument();
  const calls = [];
  installSophieR001DownloadButton({
    documentObject: fake.documentObject,
    runExport: async () => {
      calls.push('run');
      return { filename: 'BOLDUNGO_project_house_SOPHIE_R001.zip' };
    },
  });

  assert.equal(fake.button.textContent, 'Créer le ZIP pour Sophie');
  assert.equal(fake.button.options.capture, true);

  const eventCalls = [];
  await fake.button.listener({
    preventDefault: () => eventCalls.push('preventDefault'),
    stopImmediatePropagation: () => eventCalls.push('stopImmediatePropagation'),
  });

  assert.deepEqual(eventCalls, ['preventDefault', 'stopImmediatePropagation']);
  assert.deepEqual(calls, ['run']);
  assert.equal(fake.button.disabled, false);
  assert.equal(fake.status.textContent, 'ZIP prêt : BOLDUNGO_project_house_SOPHIE_R001.zip');
}

{
  const fake = fakeButtonDocument();
  installSophieR001DownloadButton({
    documentObject: fake.documentObject,
    runExport: async () => {
      throw new Error('primary_face manquant ou invalide pour DETAIL_001: null');
    },
  });

  await fake.button.listener({
    preventDefault() {},
    stopImmediatePropagation() {},
  });

  assert.match(fake.status.textContent, /Impossible de créer le ZIP/);
  assert.match(fake.status.textContent, /primary_face manquant ou invalide/);
  assert.match(fake.status.textContent, /DETAIL_001/);
  assert.equal(fake.button.disabled, false);
}

console.log('BOLDUNGO-082B5 Sophie R001 download contract passed');
