"""Conservative regression: photo-inspired preview changes only colors, not LEGO geometry."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/"frontend/progress/maison-b3-1904.ldr"
PHOTO=ROOT/"frontend/progress/maison-b3-photos-1904.ldr"

def test_photo_material_preview_keeps_all_1904_part_transforms():
    original=[l.split() for l in BASE.read_text(encoding="utf-8").splitlines() if l.startswith("1 ")]
    revised=[l.split() for l in PHOTO.read_text(encoding="utf-8").splitlines() if l.startswith("1 ")]
    assert len(original)==len(revised)==1904
    # LDraw type 1 token 1 is the color; all positions, rotations and actual part filenames are immutable.
    assert all(a[:1]+a[2:]==b[:1]+b[2:] for a,b in zip(original,revised))
    assert sum(a[1]!=b[1] for a,b in zip(original,revised))==1375
    assert all(b[1] in {"15","19","71","72","7"} for b in revised)

def test_photo_preview_explains_visual_only_status():
    js=(ROOT/"frontend/lego-progress.js").read_text(encoding="utf-8")
    html=(ROOT/"frontend/lego-progress.html").read_text(encoding="utf-8")
    assert "maison-b3-photos-1904.ldr" in js
    assert 'data-preview="photo"' in html
    assert "positions et pièces restent strictement identiques" in js
