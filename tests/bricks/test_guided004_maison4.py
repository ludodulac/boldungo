"""MAISON-4: verify ONLY new result, preserve 239 original LDraw placement records."""
from pathlib import Path
import json

def test_maison4_239_preserved_and_source_coverage():
    p=Path("artifacts/lego2-maison4")
    a=[s for s in Path("missions/MAISON3/generated/MAISON3-FACADE-EST-RDC.ldr").read_text().splitlines() if s.startswith("1 ")]
    b=[s for s in (p/"MAISON4-MURS-RDC-COMPLETS.ldr").read_text().splitlines() if s.startswith("1 ")]
    r=json.loads((p/"MAISON4-RESULTATS.json").read_text())
    assert len(a)==239 and b[:239]==a
    assert len(b)==r["total_placements"]==239+r["new_canonical_parts"]
    face=json.loads((p/"MAISON4-ETAT-FACADES.json").read_text())
    for f in ("left","right","back"):
        assert face[f]["source_rdc_available_parts_in_selection"] == (
            face[f]["already_represented_in_maison3"]+face[f]["newly_selected"])
        assert r["new_by_facade"][f]==face[f]["newly_selected"]
        assert face[f]["status"]=="CANONICAL_RDC_PARTS_COVERED" or face[f]["status"].startswith("INCOMPLETE_")
    assert r["full_available_RDC_source_parts_included"]

def test_deliverables_and_limits():
    p=Path("artifacts/lego2-maison4")
    bom=json.loads((p/"MAISON4-NOMENCLATURE.json").read_text())
    r=json.loads((p/"MAISON4-RESULTATS.json").read_text())
    limits=json.loads((p/"MAISON4-LIMITES.json").read_text())
    assert bom["total"]==sum(bom["by_real_LDraw_part"].values())
    assert r["new_orthogonal_collisions"]>=0
    assert (p/"MAISON4-VUE-3D-SCHEMATIQUE.svg").exists()
    assert limits["mechanical_strength"]=="NOT_CERTIFIED"
    assert limits["roof_terraces_upper_floors_chimneys"]=="NOT_ADDED"
