const shellStylesheetId = 'boldungo-photo-shell-styles';

if (!document.getElementById(shellStylesheetId)) {
  const link = document.createElement('link');
  link.id = shellStylesheetId;
  link.rel = 'stylesheet';
  link.href = new URL('./photo-shell.css?v=single-screen-0.8-project-flow', import.meta.url).href;
  document.head.appendChild(link);
}

import('./photo-shell.js?v=single-screen-0.8-project-controls');
import('./photo-checkpoint-flow.js?v=checkpoint-flow-0.2-state-transition');
import('./scene-correction-checkpoint.js?v=scene-correction-checkpoint-0.1');
import('./survey-import-feedback-guard.js?v=survey-feedback-0.8');
import('./copy-feedback.js?v=feedback-copy-0.1');
import('./guided-photo-ui-v1.js?v=boldungo2-guided-002');
