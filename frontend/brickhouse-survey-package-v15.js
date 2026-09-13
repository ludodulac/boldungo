// v0.15 clarifies observable glazed subdivisions on top of the active
// multi-view-aware Survey prompt without changing historical prompt layers.
import './brickhouse-survey-package-v14.js?v=pdf-handoff-0.14-multiview-identity';

const upstreamFetch = globalThis.fetch.bind(globalThis);
const openingPaneAuditUrl = new URL('./brickhouse-survey-opening-pane-audit-v40.txt', import.meta.url).href;

function absoluteUrl(input) {
  if (typeof input === 'string') return new URL(input, globalThis.location?.href || import.meta.url).href;
  if (input && typeof input.url === 'string') return input.url;
  return String(input);
}

function isSurveyPromptUrl(url) {
  try {
    return new URL(url, globalThis.location?.href || import.meta.url).pathname.endsWith('/brickhouse-survey-prompt.txt');
  } catch {
    return false;
  }
}

globalThis.fetch = async function openingPaneAwareSurveyFetch(input, init) {
  const url = absoluteUrl(input);
  const response = await upstreamFetch(input, init);
  if (!isSurveyPromptUrl(url)) return response;

  const auditResponse = await upstreamFetch(openingPaneAuditUrl, { cache: 'no-store' });
  if (!auditResponse.ok) {
    throw new Error(`Survey opening-pane addendum: HTTP ${auditResponse.status}`);
  }

  const [promptWithExistingAudits, openingPaneAudit] = await Promise.all([
    response.text(),
    auditResponse.text(),
  ]);

  return new Response(`${promptWithExistingAudits}\n\n${openingPaneAudit}`, {
    status: response.status,
    statusText: response.statusText,
    headers: response.headers,
  });
};