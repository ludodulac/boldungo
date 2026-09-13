// Stable entry point loaded by photo.html. Register the hybrid PDF generator
// first so its capture listener owns the download while the proven v0.4
// implementation remains available as historical fallback code.
import './brickhouse-survey-hybrid-pdf.js?v=pdf-handoff-0.10-hybrid-text';
import './brickhouse-survey-package-v04.js?v=pdf-handoff-0.4';
import './brickhouse-survey-package-v05.js?v=pdf-handoff-0.5-terrain-audit';
import './brickhouse-survey-package-v06.js?v=pdf-handoff-0.6-topology-audit';
import './brickhouse-survey-package-v07.js?v=pdf-handoff-0.7-coverage-audit';
import './brickhouse-survey-package-v08.js?v=pdf-handoff-0.8-final-contract-audit';
import './brickhouse-survey-package-v09.js?v=pdf-handoff-0.9-measurement-provenance';
import './brickhouse-survey-package-v11.js?v=pdf-handoff-0.11-orientation-provenance';
import './brickhouse-survey-package-v12.js?v=pdf-handoff-0.12-stair-topology';
import './brickhouse-survey-package-v13.js?v=pdf-handoff-0.13-target-context-ownership';
import './brickhouse-survey-package-v14.js?v=pdf-handoff-0.14-multiview-identity';
import './brickhouse-survey-package-v15.js?v=pdf-handoff-0.15-opening-pane-semantics';
// Reject any AI-claimed user measurement that is not exactly authorized by the
// current capture inputs before Survey validation or Scene handoff can run.
import './survey-measurement-provenance-gate.js?v=measurement-provenance-gate-0.1';
// Preserve photo capture-slot identity as provenance and reject silent facade
// permutations before Survey validation or Scene handoff can run.
import './survey-photo-orientation-provenance-gate.js?v=orientation-provenance-gate-0.1';
// Also lock Survey → Scene prompt fetches to the currently validated Survey so
// stale browser state or a model's remembered IDs cannot silently replace it.
import './scene-handoff-source-lock.js?v=scene-handoff-source-lock-0.1';
// Append the strict v4.4 serialization/contact audit to every active
// Survey → Scene prompt fetch before the handoff generator requests it.
import './scene-handoff-contract-audit-v44.js?v=scene-handoff-contract-audit-4.4';
// Make the Scene stage output-exclusive after all prior reasoning/audit layers:
// the accepted Survey is immutable input and only ArchitecturalScene may leave.
import './scene-handoff-stage-lock-v45.js?v=scene-handoff-stage-lock-4.5';
// Front-load the same stage identity immediately after the v4.3 prompt header so
// a neutral model sees the Scene output shape before it reaches Survey input data.
import './scene-handoff-output-frame-v46.js?v=scene-handoff-output-frame-4.6';
// Prevent neighboring/context objects or unresolved ownership from being silently
// metrified as target Scene primitives.
import './scene-handoff-ownership-audit-v47.js?v=scene-handoff-ownership-audit-4.7';
// Allow normal photo-only workflows to estimate a cautious common Scene scale from
// several independent architectural cues before requesting a human measurement.
import './scene-handoff-scale-audit-v48.js?v=scene-handoff-scale-audit-4.8';
// Make native external connectivity a final explicit preflight and, after a
// rejected Scene, carry the exact candidate + validator error into the next PDF.
import './scene-handoff-connectivity-audit-v49.js?v=scene-handoff-connectivity-audit-4.9';
// Intercept a Scene import when its authoritative Survey is absent so the later
// Survey importer cannot misclassify a valid Scene as a malformed Survey.
import './scene-import-routing-guard.js?v=scene-import-routing-guard-0.1';
// Preserve a validated rich Scene through the normal Build button and hand its
// BrickExportBundle directly to the existing viewer instead of degrading it to M0.
import './scene-build-direct.js?v=scene-build-direct-0.1';
// Render the images actually selected in every capture slot, including files
// inserted programmatically by the benchmark preloader.
import './photo-slot-previews.js?v=photo-slot-previews-0.1';
// Load the restored phone-first cockpit with a fresh cache key.
import './photo-shell-loader.js?v=single-screen-1.2';
// Dedicated opt-in benchmark preload. Normal photo.html visits remain untouched;
// ?benchmark=real-house-5 loads the five versioned photos, while &stage=scene
// additionally reuses the accepted Survey through the normal validation path.
import './real-house-benchmark-loader.js?v=real-house-5-preload-0.2-scene-checkpoint';
// Global product navigation is injected last and survives shell DOM changes.
import './site-nav.js?v=bh149-runtime-lock-1';