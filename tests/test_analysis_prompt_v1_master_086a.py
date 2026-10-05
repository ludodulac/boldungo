from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "frontend" / "analysis-prompt-v1-master.js"


def _preflight() -> str:
    source = MASTER.read_text(encoding="utf-8")
    start = source.index("PRÉFLIGHT AVANT SÉRIALISATION")
    end = source.index("Réponds uniquement avec le JSON ANALYSIS_RESULT V1.", start)
    return source[start:end]


def test_086a_preflight_requires_entity_by_entity_final_audit() -> None:
    preflight = _preflight()

    assert "réaudite CHAQUE ENTITY une par une, sans exception" in preflight
    assert "conditions finales de validité du JSON" in preflight


def test_086a_preflight_requires_positive_volume_evidence() -> None:
    preflight = _preflight()

    assert "VOLUME — GATE FINAL OBLIGATOIRE" in preflight
    assert "Pour chaque entity VOLUME" in preflight
    assert "preuve positive qu’un volume physique fermé ou massif existe" in preflight
    assert (
        "Des parois latérales, supports, ombres, rectangles sombres, "
        "surfaces supérieures ou occultations ne suffisent pas"
    ) in preflight
    assert "INTERDICTION de sérialiser l’entity comme VOLUME" in preflight


def test_086a_preflight_requires_demonstrated_opening_host() -> None:
    preflight = _preflight()

    assert "OPENING — GATE FINAL OBLIGATOIRE" in preflight
    assert "Pour chaque entity OPENING" in preflight
    assert "support physique ou host est lui-même démontré par les observations" in preflight
    assert "zone sombre → OPENING → donc mur ou volume hôte" in preflight
    assert "Si le host n’est pas démontré : ne sérialise pas l’entity comme OPENING" in preflight


def test_086a_preflight_requires_discriminating_multiview_identity_evidence() -> None:
    preflight = _preflight()

    assert "ENTITY MULTI-VUES — GATE FINAL OBLIGATOIRE" in preflight
    assert "Pour chaque entity regroupant des observations provenant de plusieurs photos" in preflight
    assert "indices discriminants soutenant réellement l’identité physique" in preflight
    assert "La simple ressemblance, la compatibilité de forme ou la proximité apparente ne suffisent pas" in preflight
    assert "conserve des entities séparées" in preflight
    assert "crée une uncertainty appropriée" in preflight


def test_086a_preflight_preserves_negative_space_under_supporting_structures() -> None:
    preflight = _preflight()

    assert "ESPACE NÉGATIF / STRUCTURE PORTEUSE — GATE FINAL OBLIGATOIRE" in preflight
    assert "Préserve tout espace négatif ou ouvert soutenu par les observations" in preflight
    assert (
        "Une surface élevée, des murs latéraux, des poteaux, des supports "
        "ou d’autres éléments porteurs ne doivent jamais forcer l’existence "
        "d’un volume fermé sous la structure"
    ) in preflight


def test_086a_preflight_contains_no_house_or_benchmark_leakage() -> None:
    preflight = _preflight().casefold()

    forbidden = (
        "real-house-5",
        "real-house-5-3plus1",
        "run_a",
        "run_b",
        "run_c",
        "front_001",
        "right_001",
        "left_001",
        "left_002",
        "rear_001",
        "arbiter",
        "finding",
        "pavés de verre",
        "paves de verre",
    )
    for marker in forbidden:
        assert marker not in preflight
