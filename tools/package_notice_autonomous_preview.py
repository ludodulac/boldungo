#!/usr/bin/env python3
"""Package the experimental autonomous NOTICE preview as one file:// HTML.

Packaging only: viewer.js remains the renderer source of truth.
Three.js and OrbitControls intentionally remain on the existing jsDelivr CDN.
"""
from pathlib import Path
import json, re

ROOT = Path(__file__).resolve().parents[1]
html = (ROOT / "frontend/viewer.html").read_text(encoding="utf-8")
js = (ROOT / "frontend/viewer.js").read_text(encoding="utf-8")
css = (ROOT / "frontend/styles.css").read_text(encoding="utf-8")
data_text = (ROOT / "frontend/notice-autonomous-preview-export.json").read_text(encoding="utf-8")
data = json.loads(data_text)

steps = data["assembly_plan"]["steps"]
assert len(steps) == 5
assert steps[0]["placement_ids"] == ["wall-000001"]
assert [s["placement_ids"] for s in steps] == [
    ["wall-000001"],
    ["wall-000017", "wall-000016"],
    ["wall-000041"],
    ["wall-000063"],
    ["wall-000002"],
]

# Keep the real renderer; replace only the preview's local JSON fetch with embedded data.
embedded = data_text.replace("</", "<\\/")
js = js.replace(
    "async function loadAutonomousPreview(){try{const r=await fetch('./notice-autonomous-preview-export.json',{cache:'no-store'});if(!r.ok)throw new Error(\`HTTP \${r.status}\`);renderBundle(await r.json(),{persist:false});showAssemblyStep(0);}catch(e){setMessage(\`NOTICE autonome indisponible : \${e.message}\`);}}",
    "async function loadAutonomousPreview(){try{const data=JSON.parse(document.querySelector('#autonomous-preview-data').textContent);renderBundle(data,{persist:false});showAssemblyStep(0);}catch(e){setMessage(\`NOTICE autonome indisponible : \${e.message}\`);}}",
)
if "fetch('./notice-autonomous-preview-export.json'" in js:
    raise SystemExit("preview fetch replacement failed")

# file:// entry has no query string: force only the existing autonomous-preview route.
js = js.replace(
    "const PLATE_WORLD_HEIGHT=1/2.5;const noticeMode=new URLSearchParams(window.location.search).get('notice');",
    "const PLATE_WORLD_HEIGHT=1/2.5;const noticeMode='autonomous-preview';",
    1,
)

# Inline local CSS and the real viewer.js. Auxiliary product modules are unnecessary
# for this temporary preview and would create file:// module requests.
html = html.replace('<link rel="stylesheet" href="./styles.css" />', f"<style>\\n{css}\\n</style>")
html = html.replace(
    '    <script type="module" src="./viewer.js"></script>\\n'
    '    <script type="module" src="./viewer-precision.js"></script>\\n'
    '    <script type="module" src="./reference-loader.js"></script>\\n'
    '    <script type="module" src="./site-nav.js?v=bh147-global-nav-1"></script>',
    f'    <script id="autonomous-preview-data" type="application/json">{{embedded}}</script>\\n'
    f'    <script type="module">\\n{{js}}\\n</script>',
)
if "./viewer.js" in html or "./styles.css" in html:
    raise SystemExit("local frontend resource remained")

out = ROOT / "frontend/notice-autonomous-preview-standalone.html"
out.write_text(html, encoding="utf-8")
print(f"wrote {out} ({out.stat().st_size} bytes)")
