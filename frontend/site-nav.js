const NAV_ITEMS = [
  { group: 'Parcours principal', href: './index.html', label: 'Accueil' },
  { group: 'Parcours principal', href: './photo.html', label: '1. Photos → Relevé' },
  { group: 'Parcours principal', href: './scene.html?benchmark=real-house-5&stage=scene', label: '2. Relevé → Scene 3D' },
  { group: 'Parcours principal', href: './configurator.html', label: 'Configurateur manuel LEGO' },
  { group: 'Parcours principal', href: './viewer.html', label: 'Visionneuse du modèle LEGO' },
  { group: 'Parcours principal', href: './instructions.html', label: 'Notice de montage' },
  { group: 'Parcours principal', href: './viewer.html?notice=step-0001', label: 'Aperçu NOTICE — étape 1' },
  { group: 'Outils et diagnostics', href: './scene-viewer.html', label: 'Visionneuse Scene 3D' },
  { group: 'Outils et diagnostics', href: './brickhouse-first-bricks.html', label: 'Diagnostic · premières briques' },
  { group: 'Outils et diagnostics', href: './brickhouse-reference-preview.html', label: 'Prévisualisation de référence' },
  { group: 'Outils et diagnostics', href: './brickhouse-rich-scene-preview.html', label: 'Démo Scene 3D riche' },
];

const STYLE_ID = 'boldungo-site-nav-style';
const ROOT_ID = 'boldungo-site-nav';

function currentFile() {
  const name = new URL(globalThis.location.href).pathname.split('/').pop();
  return name || 'index.html';
}

function setTextIfChanged(element, text) {
  if (element && element.textContent !== text) element.textContent = text;
}

function normalizePrimaryActions() {
  const file = currentFile();
  if (file === 'photo.html') {
    setTextIfChanged(document.querySelector('#download-ai-package'), 'Créer le PDF Photos → Relevé');
  }
  if (file === 'scene.html') {
    setTextIfChanged(document.querySelector('#download-scene-handoff'), 'Créer le PDF Relevé → Scene 3D');
  }
}

function addStyles() {
  if (document.getElementById(STYLE_ID)) return;
  const style = document.createElement('style');
  style.id = STYLE_ID;
  style.textContent = `
    .site-nav-root{position:fixed;top:14px;right:14px;z-index:1000;font-family:system-ui,sans-serif;pointer-events:none}
    .site-nav-toggle{width:48px;height:48px;border:0;border-radius:14px;background:#132039;color:#fff;box-shadow:0 6px 24px #0003;cursor:pointer;display:grid;place-items:center;font-size:0;pointer-events:auto}
    .site-nav-toggle span,.site-nav-toggle span::before,.site-nav-toggle span::after{display:block;width:23px;height:2px;background:currentColor;border-radius:2px;content:'';position:relative}
    .site-nav-toggle span::before{position:absolute;top:-7px}.site-nav-toggle span::after{position:absolute;top:7px}
    .site-nav-panel{position:absolute;right:0;top:56px;width:min(330px,calc(100vw - 28px));max-height:calc(100vh - 84px);overflow:auto;background:#fff;color:#132039;border:1px solid #d9e1ec;border-radius:16px;box-shadow:0 16px 46px #0003;padding:12px;pointer-events:auto}
    .site-nav-panel[hidden]{display:none;pointer-events:none}
    .site-nav-title{font-weight:800;padding:8px 10px 12px}
    .site-nav-group{margin:8px 0}.site-nav-group-title{font-size:.72rem;letter-spacing:.08em;text-transform:uppercase;color:#667085;padding:7px 10px 4px}
    .site-nav-link{display:block;color:#132039;text-decoration:none;padding:10px;border-radius:10px;font-weight:650}
    .site-nav-link:hover,.site-nav-link:focus-visible{background:#edf2f7;outline:none}.site-nav-link[aria-current=page]{background:#132039;color:#fff}
  `;
  document.head.append(style);
}

function buildNav() {
  if (document.getElementById(ROOT_ID)) return;
  addStyles();
  const root = document.createElement('div');
  root.id = ROOT_ID;
  root.className = 'site-nav-root';

  const toggle = document.createElement('button');
  toggle.type = 'button';
  toggle.className = 'site-nav-toggle';
  toggle.setAttribute('aria-label', 'Ouvrir le menu');
  toggle.setAttribute('aria-expanded', 'false');
  toggle.setAttribute('aria-controls', 'site-menu-panel');
  toggle.innerHTML = '<span aria-hidden="true"></span>';

  const panel = document.createElement('nav');
  panel.id = 'site-menu-panel';
  panel.className = 'site-nav-panel';
  panel.setAttribute('aria-label', 'Navigation principale');
  panel.hidden = true;
  panel.innerHTML = '<div class="site-nav-title">Toutes les pages Boldungo</div>';

  const file = currentFile();
  for (const groupName of [...new Set(NAV_ITEMS.map(item => item.group))]) {
    const group = document.createElement('div');
    group.className = 'site-nav-group';
    group.innerHTML = `<div class="site-nav-group-title">${groupName}</div>`;
    for (const item of NAV_ITEMS.filter(candidate => candidate.group === groupName)) {
      const link = document.createElement('a');
      link.className = 'site-nav-link';
      link.href = item.href;
      link.textContent = item.label;
      const targetFile = new URL(item.href, globalThis.location.href).pathname.split('/').pop();
      if (targetFile === file) link.setAttribute('aria-current', 'page');
      group.append(link);
    }
    panel.append(group);
  }

  const setOpen = open => {
    panel.hidden = !open;
    toggle.setAttribute('aria-expanded', String(open));
    toggle.setAttribute('aria-label', open ? 'Fermer le menu' : 'Ouvrir le menu');
    if (open) panel.querySelector('a')?.focus();
  };
  toggle.addEventListener('click', () => setOpen(panel.hidden));
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && !panel.hidden) {
      setOpen(false);
      toggle.focus();
    }
  });
  document.addEventListener('pointerdown', event => {
    if (!panel.hidden && !root.contains(event.target)) setOpen(false);
  });

  root.append(toggle, panel);
  document.body.append(root);
}

function ensureNav() {
  if (!document.body) return;
  normalizePrimaryActions();
  buildNav();
}

if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', ensureNav, { once: true });
else ensureNav();

// BH-231: do not keep an unbounded document-wide MutationObserver alive here.
// The photo/scene primary controls already exist when this module is loaded, and
// moving those controls into the shell does not change their label. A second
// one-shot normalization at window load covers late DOM initialization without
// creating a feedback path that can starve ordinary clicks or keep headless
// Chrome spinning after the page has otherwise settled.
if (document.readyState !== 'complete') {
  globalThis.addEventListener('load', ensureNav, { once: true });
}
