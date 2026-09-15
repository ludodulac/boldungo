const gateImportButton = document.querySelector('#import-analysis');
const gateExternalInput = document.querySelector('#external-analysis');
const gateApiInput = document.querySelector('#api-url');
const gateStuds = document.querySelector('#studs');
const gateStatus = document.querySelector('#status');
const gateEmpty = document.querySelector('#empty-state');
const gateResult = document.querySelector('#result');
const gateResultName = document.querySelector('#result-name');
const gateConfidence = document.querySelector('#confidence');
const gateConfirmation = document.querySelector('#confirmation-card');
const gateQuestions = document.querySelector('#questions');
const gateAssumptions = document.querySelector('#assumptions');
const gateProportions = document.querySelector('#proportions-card');
const gateScaleBasis = document.querySelector('#scale-basis');
const gateEvidence = document.querySelector('#proportion-evidence');
const gatePreview = document.querySelector('#json-preview');
const gateDownload = document.querySelector('#download-model');
const gateReport = document.querySelector('#download-report');
const gateBuild = document.querySelector('#build-bricks');

let sceneProgressTimer = null;
let sceneProgressTimeout = null;
let sceneStatusWatchdog = null;
let protectSceneStatus = false;
let lastSceneStatus = '';
let currentSceneBuildPayload = null;
const IDLE_STATUS_PREFIX = 'Ajoutez vos photos puis lancez l’analyse';
const VALIDATION_TIMEOUT_MS = 45000;

function gateApiBase() { return gateApiInput.value.trim().replace(/\/$/, ''); }
function gateEscape(value) { return String(value).replace(/[&<>\"]/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '\"': '&quot;' }[char])); }
function gateExtractJson(raw) {
  const value = raw.trim();
  const start = value.indexOf('{');
  if (start < 0) return value;
  let depth = 0, inString = false, escaped = false;
  for (let index = start; index < value.length; index += 1) {
    const char = value[index];
    if (inString) {
      if (escaped) escaped = false;
      else if (char === '\\') escaped = true;
      else if (char === '\"') inString = false;
      continue;
    }
    if (char === '\"') { inString = true; continue; }
    if (char === '{') depth += 1;
    else if (char === '}' && --depth === 0) return value.slice(start, index + 1);
  }
  return value.slice(start);
}
function pendingSurvey() {
  try {
    const payload = JSON.parse(localStorage.getItem('brickhouse.pendingArchitecturalSurvey') || 'null');
    return payload?.valid_for_scene_fusion ? payload.survey : null;
  } catch { return null; }
}
function hydrateCertainSurveyRelations(survey, scene) {
  const hydrated = JSON.parse(JSON.stringify(scene));
  const relations = Array.isArray(hydrated.relations) ? [...hydrated.relations] : [];
  const existingIds = new Set(relations.map(item => item?.id).filter(Boolean));
  const objectIds = new Set();
  for (const key of ['volumes', 'openings', 'roofs', 'chimneys', 'platforms', 'stairs', 'equipment']) {
    for (const item of hydrated[key] ?? []) {
      if (item?.id) objectIds.add(item.id);
      if (key === 'platforms') for (const support of item?.supports ?? []) if (support?.id) objectIds.add(support.id);
    }
  }
  const realizedSurveyIds = new Set(
    (hydrated.survey_realizations ?? [])
      .filter(item => Array.isArray(item?.scene_object_ids) && item.scene_object_ids.length > 0)
      .filter(item => item.scene_object_ids.every(id => objectIds.has(id)))
      .map(item => item.survey_observation_id)
      .filter(Boolean),
  );
  const endpointIsRepresented = id => objectIds.has(id) || realizedSurveyIds.has(id);
  for (const relation of survey?.relations ?? []) {
    if (relation?.certainty !== 'certain' || existingIds.has(relation.id)) continue;
    if (!endpointIsRepresented(relation.subject_id) || !endpointIsRepresented(relation.object_id)) continue;
    relations.push({
      id: relation.id,
      kind: relation.kind,
      subject_id: relation.subject_id,
      object_id: relation.object_id,
      certainty: 'certain',
      geometry_status: 'unresolved',
      statement: relation.statement,
      evidence: (relation.evidence ?? []).map(item => ({ photo_index: item.photo_index, observation: item.observation })),
    });
    existingIds.add(relation.id);
  }
  hydrated.relations = relations;
  return hydrated;
}
function formatValidationDetail(detail) {
  if (typeof detail === 'string') return detail;
  if (!Array.isArray(detail)) return 'La scène ne respecte pas le contrat BrickHouse.';
  return detail.slice(0, 8).map(item => {
    const path = Array.isArray(item.loc) ? item.loc.filter(part => part !== 'body').join('.') : 'champ inconnu';
    return `${path || 'racine'} : ${item.msg || item.type || 'valeur invalide'}`;
  }).join(' · ');
}
function formatSurveyIssue(issue) {
  const object = issue.object_id ? ` [${issue.object_id}]` : '';
  const code = issue.code ? `${issue.code}${object}` : (issue.object_id || 'issue');
  return `${code} : ${issue.message}`;
}
function isIdleStatus(text) { return String(text || '').trim().startsWith(IDLE_STATUS_PREFIX); }
function rememberSceneStatus(text) {
  const value = String(text || '').trim();
  if (!value || isIdleStatus(value) || value.startsWith('Vérification du moteur BrickHouse')) return;
  lastSceneStatus = value;
}
function restoreSceneStatusIfNeeded() {
  if (protectSceneStatus && lastSceneStatus && isIdleStatus(gateStatus.textContent)) gateStatus.textContent = lastSceneStatus;
}
function startSceneStatusProtection() {
  protectSceneStatus = true;
  if (sceneStatusWatchdog) clearInterval(sceneStatusWatchdog);
  sceneStatusWatchdog = setInterval(restoreSceneStatusIfNeeded, 250);
}
function stopSceneStatusProtection() {
  protectSceneStatus = false;
  lastSceneStatus = '';
  if (sceneStatusWatchdog) clearInterval(sceneStatusWatchdog);
  sceneStatusWatchdog = null;
}
const statusObserver = new MutationObserver(() => {
  if (!protectSceneStatus) return;
  const text = gateStatus.textContent || '';
  if (isIdleStatus(text)) queueMicrotask(restoreSceneStatusIfNeeded);
  else rememberSceneStatus(text);
});
statusObserver.observe(gateStatus, { childList: true, characterData: true, subtree: true });
gateExternalInput?.addEventListener('input', () => {
  if (!gateExternalInput.value.trim()) stopSceneStatusProtection();
});

function stopSceneProgress() {
  if (sceneProgressTimer) clearInterval(sceneProgressTimer);
  if (sceneProgressTimeout) clearTimeout(sceneProgressTimeout);
  sceneProgressTimer = null;
  sceneProgressTimeout = null;
}
function startSceneProgress(label) {
  stopSceneProgress();
  const frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'];
  let index = 0;
  const update = () => {
    gateStatus.textContent = `${frames[index % frames.length]} ${label} en cours…`;
    rememberSceneStatus(gateStatus.textContent);
    index += 1;
  };
  update();
  sceneProgressTimer = setInterval(update, 180);
}
async function postJsonWithTimeout(url, body) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), VALIDATION_TIMEOUT_MS);
  try {
    return await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: controller.signal,
    });
  } finally {
    clearTimeout(timer);
  }
}
function renderFinalSceneValidation(payload) {
  const scene = payload.scene;
  const survey = pendingSurvey();
  const building = payload.projection?.building ?? null;
  const compatibility = payload.m0_compatibility ?? { buildable: false, blockers: ['Aucune projection BuildingModel constructible.'], warnings: [] };
  const projectionIssues = payload.projection?.issues ?? [];
  const blockers = [...(compatibility.blockers ?? []), ...projectionIssues.filter(item => item.severity === 'blocker').map(item => item.message)];
  const warnings = [...(compatibility.warnings ?? []), ...projectionIssues.filter(item => item.severity === 'warning').map(item => item.message)];
  const buildable = Boolean(building && compatibility.buildable && !blockers.length);
  const sceneOpeningIds = new Set((scene.openings ?? []).map(item => item.id));
  const omittedCertainOpenings = (survey?.observations ?? [])
    .filter(item => item.kind === 'opening' && item.certainty === 'certain' && !sceneOpeningIds.has(item.id))
    .map(item => item.id);

  currentSceneBuildPayload = buildable ? payload : null;
  gateEmpty.hidden = true;
  gateResult.hidden = false;
  gateResultName.textContent = scene.name;
  gateConfidence.textContent = 'Scène v0.2';
  gateConfirmation.hidden = false;
  gateConfirmation.innerHTML = blockers.length
    ? `<h3>Scène valide, projection M0 bloquée</h3><p>${blockers.map(gateEscape).join(' ')}</p>`
    : warnings.length
      ? `<h3>Scène riche validée — simplifications M0 visibles</h3><p>${warnings.map(gateEscape).join(' ')}</p>`
      : '<h3>Scène validée</h3><p>Aucune perte de projection signalée.</p>';
  gateQuestions.innerHTML = buildable
    ? '<p><strong>Étape suivante :</strong> cliquez sur « Construire cette proposition » pour générer la maquette et ouvrir le viewer.</p>'
    : '<p>La cohérence Survey → Scene et la validation géométrique sont terminées. Corrigez les blocages affichés avant la construction.</p>';
  const facts = [
    scene.terrain?.profiles?.length ? `${scene.terrain.profiles.length} profil(s) de terrain conservé(s) dans ArchitecturalScene.` : null,
    scene.chimneys?.length ? `${scene.chimneys.length} cheminée(s) conservée(s) dans ArchitecturalScene.` : null,
    scene.platforms?.length ? `${scene.platforms.length} plateforme(s)/terrasse(s) conservée(s) dans ArchitecturalScene.` : null,
    scene.stairs?.length ? `${scene.stairs.length} tronçon(s) d’escalier conservé(s) dans ArchitecturalScene.` : null,
    scene.visibility?.length ? `${scene.visibility.length} façade(s) avec information de visibilité/occlusion dans ArchitecturalScene.` : null,
    omittedCertainOpenings.length ? `Observé(s) avec certitude dans le Survey mais non matérialisé(s) dans ArchitecturalScene : ${omittedCertainOpenings.join(', ')}. Ces éléments restent des faits du relevé et ne doivent pas être considérés comme absents de la maison.` : null,
    ...warnings.map(item => `Limite de projection M0 (la Scene reste la source riche) : ${item}`),
  ].filter(Boolean);
  gateAssumptions.innerHTML = facts.length ? facts.map(item => `<li>${gateEscape(item)}</li>`).join('') : '<li>Aucune perte de scène signalée.</li>';
  const width = scene.volumes?.[0]?.width;
  gateProportions.hidden = !width;
  gateScaleBasis.textContent = width ? `Largeur principale : ${width.value} m · ${width.source.kind} · confiance ${Math.round((width.source.confidence ?? 0) * 100)} %` : '';
  if (width?.evidence?.length) {
    gateEvidence.innerHTML = width.evidence.map(item => `<li>Photo ${item.photo_index} — ${gateEscape(item.observation)}</li>`).join('');
  } else if (width?.source?.kind === 'user_provided') {
    gateEvidence.innerHTML = `<li>Ancre d’échelle explicite fournie par l’utilisateur : largeur de façade = ${gateEscape(width.value)} m. L’absence d’evidence photographique ne remet pas en cause cette mesure utilisateur.</li>`;
  } else {
    gateEvidence.innerHTML = '<li>Aucune preuve d’échelle explicite disponible pour cette dimension estimée.</li>';
  }
  gatePreview.textContent = JSON.stringify(scene, null, 2);
  gateDownload.disabled = true;
  gateReport.disabled = true;
  gateBuild.disabled = !buildable;
  localStorage.setItem('brickhouse.pendingSceneValidation', JSON.stringify(payload));
  gateStatus.textContent = buildable
    ? 'ArchitecturalScene valide et constructible. Étape suivante : cliquez sur « Construire cette proposition ».'
    : building
      ? 'ArchitecturalScene valide, mais le moteur M0 signale encore un blocage de construction. Consultez les raisons affichées.'
      : 'ArchitecturalScene valide, mais la projection vers le moteur M0 est bloquée. Consultez les raisons affichées.';
  rememberSceneStatus(gateStatus.textContent);
}

gateBuild.addEventListener('click', async event => {
  const payload = currentSceneBuildPayload;
  const scene = payload?.scene ?? null;
  if (!scene) return;
  event.preventDefault();
  event.stopImmediatePropagation();
  const base = gateApiBase();
  if (!base) { gateStatus.textContent = 'URL API manquante.'; return; }
  gateBuild.disabled = true;
  gateStatus.textContent = 'BrickHouse génère maintenant la maquette constructible à partir de la Scene complète…';
  rememberSceneStatus(gateStatus.textContent);
  try {
    const response = await postJsonWithTimeout(`${base}/api/v1/build-scene`, {
      scene,
      front_width_studs: Number(gateStuds?.value) || 48,
    });
    const exportPayload = await response.json();
    if (!response.ok) {
      const detail = typeof exportPayload.detail === 'string' ? exportPayload.detail : `Erreur moteur HTTP ${response.status}`;
      throw new Error(detail);
    }
    localStorage.setItem('brickhouse.pendingArchitecturalScene', JSON.stringify(payload));
    localStorage.setItem('brickhouse.pendingExport', JSON.stringify(exportPayload));
    window.location.href = './viewer.html';
  } catch (error) {
    const timeout = error.name === 'AbortError';
    gateStatus.textContent = timeout
      ? 'Construction interrompue après 45 s : le moteur n’a pas répondu. Réessayez.'
      : `Construction impossible : ${error.message}`;
    rememberSceneStatus(gateStatus.textContent);
    gateBuild.disabled = false;
  }
}, { capture: true });

gateImportButton.addEventListener('click', async event => {
  let parsed;
  try { parsed = JSON.parse(gateExtractJson(gateExternalInput.value)); } catch { return; }
  const isScene = parsed?.schema_version === '0.2' && Array.isArray(parsed?.volumes) && !parsed?.building;
  const survey = pendingSurvey();
  if (!isScene || !survey) return;

  event.preventDefault();
  event.stopImmediatePropagation();
  const base = gateApiBase();
  if (!base) { gateStatus.textContent = 'URL API manquante.'; return; }
  startSceneStatusProtection();
  currentSceneBuildPayload = null;
  gateImportButton.disabled = true;
  gateBuild.disabled = true;
  parsed = hydrateCertainSurveyRelations(survey, parsed);

  try {
    startSceneProgress('Contrôle Survey → Scene');
    const surveyResponse = await postJsonWithTimeout(`${base}/api/v1/validate-scene-against-survey`, { survey, scene: parsed });
    const surveyPayload = await surveyResponse.json();
    if (!surveyResponse.ok) throw new Error(formatValidationDetail(surveyPayload.detail));

    const surveyErrors = (surveyPayload.issues ?? []).filter(item => item.severity === 'error');
    localStorage.setItem('brickhouse.lastSceneSurveyValidation', JSON.stringify(surveyPayload));
    if (surveyErrors.length) {
      throw new Error(`Scène refusée par le Survey : ${surveyErrors.map(formatSurveyIssue).join(' · ')}`);
    }

    if (!surveyPayload.valid_for_projection && surveyPayload.projection) {
      stopSceneProgress();
      renderFinalSceneValidation(surveyPayload);
      return;
    }

    startSceneProgress('Validation géométrique finale');
    const sceneResponse = await postJsonWithTimeout(`${base}/api/v1/validate-scene`, parsed);
    const scenePayload = await sceneResponse.json();
    if (!sceneResponse.ok) throw new Error(formatValidationDetail(scenePayload.detail));

    stopSceneProgress();
    renderFinalSceneValidation(scenePayload);
  } catch (error) {
    stopSceneProgress();
    const timeout = error.name === 'AbortError';
    gateStatus.textContent = timeout
      ? 'Validation interrompue après 45 s : le serveur n’a pas répondu à une étape précise. Ne construisez pas.'
      : `Validation impossible : ${error.message}`;
    rememberSceneStatus(gateStatus.textContent);
  } finally {
    gateImportButton.disabled = false;
  }
}, { capture: true });
