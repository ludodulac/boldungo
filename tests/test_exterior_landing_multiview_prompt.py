from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROMPT = ROOT / "frontend" / "brickhouse-survey-prompt.txt"


def test_survey_separates_walkable_landing_from_support_volume() -> None:
    source = PROMPT.read_text(encoding="utf-8")
    assert "PROMPT DE RELEVÉ ARCHITECTURAL v2.9" in source
    assert "DÉCOMPOSITION PALIER / VOLUME PORTEUR / TERRASSE" in source
    assert "surface horizontale praticable distincte" in source
    assert 'observation `kind:"platform"` distincte du volume/support' in source
    assert "n’autorise jamais à l’absorber dans `kind:\"volume\"`" in source


def test_survey_preserves_stair_landing_deck_topology_before_metrics() -> None:
    source = PROMPT.read_text(encoding="utf-8")
    assert "DEUX primitives (`stair` + `platform`)" in source
    assert "Ne remplace pas ce palier par une connexion directe escalier→bâtiment" in source
    assert "terrasse bois et un palier béton restent deux objets" in source
    assert "relation palier→l’observation `building_boundary` correspondante" in source
    assert "Ne déduis pas automatiquement terrasse→bâtiment ou escalier→bâtiment" in source
    assert "N’invente jamais une volée cachée" in source


def test_final_audit_rejects_collapsing_distinct_exterior_circulation_surfaces() -> None:
    source = PROMPT.read_text(encoding="utf-8")
    assert "toute surface de circulation extérieure distincte visuellement" in source
    assert "un escalier aboutissant visiblement sur un palier conserve la relation escalier→palier" in source
    assert "deux plateformes de matériaux/fonctions distincts restent deux objets" in source
