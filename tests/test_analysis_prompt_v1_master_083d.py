import hashlib
import json
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

from brickhouse.blind_benchmark_v1 import build_real_house_5_p2_blind_package


ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
MASTER_SOURCE = FRONTEND / "analysis-prompt-v1-master.js"
BENCHMARK_ROOT = FRONTEND / "benchmarks" / "real-house-5"
PHOTO = BENCHMARK_ROOT / "02-original.jpg"
EVALUATOR = BENCHMARK_ROOT / "evaluator" / "blind-p2-evaluator-v0.1.json"

PACKAGE_ID = "PKG_123e4567-e89b-42d3-a456-426614174000"
PHOTO_SHA256 = "490a9058e9de9b689860256e4b9bb22f16111256106cc48fd90612c5ae3c6ec3"

HISTORICAL_SOURCES = (
    "brickhouse-survey-prompt.txt",
    "brickhouse-topology-prompt.txt",
    "brickhouse-survey-terrain-audit-v29.txt",
    "brickhouse-survey-topology-audit-v30.txt",
    "brickhouse-survey-reasoning-audit-v34.txt",
    "brickhouse-survey-measurement-provenance-audit-v35.txt",
    "brickhouse-survey-orientation-provenance-audit-v36.txt",
    "brickhouse-survey-stair-topology-audit-v37.txt",
    "brickhouse-survey-ownership-audit-v38.txt",
    "brickhouse-survey-multiview-identity-audit-v39.txt",
)

PROMPT_BENCHMARK_LEAK_MARKERS = (
    "real-house-5",
    "right-opening-",
    "front_001",
    "glass_block",
    "pavés de verre",
    "paves de verre",
    "local_grade_clearance",
    "petite ouverture basse proche",
    "autre ouverture basse",
    "blocs translucides",
    "montée le long de la face droite",
    "montee le long de la face droite",
    "terrain montant vers l'arrière",
    "terrain montant vers l’arrière",
)

PACKAGE_TRUTH_LEAK_MARKERS = tuple(
    marker for marker in PROMPT_BENCHMARK_LEAK_MARKERS if marker != "real-house-5"
)

OLD_SURVEY_OUTPUT_MARKERS = (
    "ArchitecturalSurvey",
    "known_measurements",
    "attribute_certainty",
    "canonical_frame",
    "representation_policy",
    "physical_objects",
    '"schema_version": "0.1"',
)


def _master_package():
    built = build_real_house_5_p2_blind_package(
        package_id=PACKAGE_ID,
        prompt_variant="master",
    )
    return built, ZipFile(BytesIO(built.zip_bytes), "r")


def _master_prompt_from_package() -> str:
    _, archive = _master_package()
    with archive:
        return archive.read("prompt.txt").decode("utf-8")


def test_all_required_historical_prompt_sources_remain_available() -> None:
    for relative in HISTORICAL_SOURCES:
        assert (FRONTEND / relative).is_file()


def test_master_prompt_uses_only_v1_analysis_result_output_contract() -> None:
    prompt = _master_prompt_from_package()

    assert 'schema_version = "boldungo.exchange.v1"' in prompt
    assert 'message_type = "ANALYSIS_RESULT"' in prompt
    assert "payload contient exactement" in prompt
    assert "analysis contient exactement" in prompt

    required_families = (
        "observations",
        "human_facts",
        "entities",
        "relations",
        "uncertainties",
        "questions",
    )
    for family in required_families:
        assert family in prompt

    for marker in OLD_SURVEY_OUTPUT_MARKERS:
        assert marker not in prompt


def test_master_prompt_preserves_topology_multiview_occlusion_and_attribute_reasoning() -> None:
    prompt = _master_prompt_from_package()

    assert "TOPOLOGIE AVANT MÉTRIQUE" in prompt
    assert "quels objets physiques existent" in prompt
    assert "quelles relations spatiales ou topologiques" in prompt

    assert "IDENTITÉ MULTI-VUES" in prompt
    assert "détail de forme stable" in prompt
    assert "position relative par rapport à des ancres communes" in prompt
    assert "continuité structurelle" in prompt
    assert "occlusion cohérente" in prompt
    assert "transition observable d’une façade à une autre" in prompt
    assert "Ne fusionne jamais deux occurrences sur simple ressemblance" in prompt

    assert "OCCLUSION ≠ ABSENCE" in prompt
    assert "Une zone cachée, hors champ, masquée ou tronquée reste inconnue" in prompt

    assert "OBJET ≠ ATTRIBUT" in prompt
    assert "L’existence d’un objet et la certitude de ses attributs" in prompt


def test_master_prompt_preserves_stair_terrain_ownership_and_relation_rules() -> None:
    prompt = _master_prompt_from_package()

    assert "ESCALIERS" in prompt
    assert "changement de direction" in prompt
    assert "une seule ligne droite" in prompt
    assert "système architectural d’escalier" in prompt
    assert "portions ou volées réellement distinguables" in prompt

    assert "TERRAIN / TROTTOIR / ROUTE" in prompt
    assert "grade visible" in prompt
    assert "grade non soutenu" in prompt
    assert "grade occulté ou ambigu" in prompt
    assert "Une direction qualitative de montée ou descente" in prompt
    for forbidden_metric in ("angle", "pourcentage", "élévation", "mètres"):
        assert forbidden_metric in prompt

    assert "OWNERSHIP — BÂTIMENT CIBLE VS CONTEXTE" in prompt
    assert "objet appartenant au bâtiment cible" in prompt
    assert "objet appartenant au contexte extérieur" in prompt
    assert "appartenance non résolue" in prompt

    assert "Les relations ne sont jamais transitives par défaut" in prompt


def test_master_prompt_uses_strict_triple_question_gate() -> None:
    prompt = _master_prompt_from_package()

    assert "MATERIAL_IMPACT" in prompt
    assert "PHOTO_INSUFFICIENT" in prompt
    assert "HUMAN_KNOWABLE" in prompt
    assert "simultanément vraies" in prompt
    assert "coordonnées LEGO" in prompt
    assert "studs" in prompt
    assert "plates" in prompt
    assert "une valeur métrique qu’il devrait estimer ou deviner sur la photo" in prompt


def test_master_prompt_covers_generic_architectural_modules_without_presupposing_presence() -> None:
    prompt = _master_prompt_from_package()

    assert "MODULES À AUDITER SANS PRÉSUPPOSER LEUR PRÉSENCE" in prompt
    for module in (
        "volumes principaux ou secondaires",
        "toiture",
        "ouvertures",
        "plateforme ou terrasse maçonnée",
        "escalier et système de volées",
        "terrasse bois ou deck",
        "supports ou poteaux",
        "garde-corps ou murets",
        "terrain, trottoir ou route",
        "cheminées ou équipements",
        "objets de contexte",
    ):
        assert module in prompt
    assert "L’absence d’un module dans les images signifie : ne pas l’inventer." in prompt


def test_master_prompt_human_facts_are_history_only_not_photo_inference() -> None:
    prompt = _master_prompt_from_package()

    assert "human_facts contient uniquement des faits issus de réponses humaines antérieures" in prompt
    assert "Ne crée jamais de human_fact depuis une photo" in prompt
    assert "Si aucun historique V1 de réponses humaines n’est fourni dans le package, human_facts doit être []" in prompt


def test_master_prompt_has_no_real_house_or_human_truth_leak() -> None:
    prompt = _master_prompt_from_package().casefold()
    source = MASTER_SOURCE.read_text(encoding="utf-8").casefold()

    for marker in PROMPT_BENCHMARK_LEAK_MARKERS:
        assert marker.casefold() not in prompt
        assert marker.casefold() not in source


def test_blind_p2_master_package_keeps_exact_challenge_content_and_photo_bytes() -> None:
    built, archive = _master_package()
    with archive:
        assert built.filename == "BOLDUNGO_REAL-HOUSE-5-P2-BLIND_SOPHIE_R001.zip"
        assert set(archive.namelist()) == {
            "manifest.json",
            "prompt.txt",
            "photos/RIGHT_001.jpg",
        }

        manifest = json.loads(archive.read("manifest.json"))
        assert manifest["schema_version"] == "boldungo.analysis-package-manifest.v1"
        assert manifest["project_id"] == "REAL-HOUSE-5-P2-BLIND"
        assert manifest["agent_id"] == "SOPHIE"
        assert manifest["agent_display_name"] == "Sophie"
        assert manifest["round_id"] == "R001"
        assert manifest["package_id"] == PACKAGE_ID
        assert manifest["prompt_path"] == "prompt.txt"
        assert manifest["photos"] == [
            {
                "photo_id": "RIGHT_001",
                "file_path": "photos/RIGHT_001.jpg",
                "primary_face": "RIGHT",
                "original_filename": "02-original.jpg",
                "note": None,
            }
        ]

        source_photo = PHOTO.read_bytes()
        packaged_photo = archive.read("photos/RIGHT_001.jpg")
        assert packaged_photo == source_photo
        assert hashlib.sha256(packaged_photo).hexdigest() == PHOTO_SHA256

        assert not any("evaluator" in name.casefold() for name in archive.namelist())
        assert EVALUATOR.name not in archive.namelist()


def test_master_variant_does_not_change_blind_evaluator_or_challenge_identity() -> None:
    evaluator_before = json.loads(EVALUATOR.read_text(encoding="utf-8"))
    assert evaluator_before["benchmark_id"] == "REAL-HOUSE-5-P2-BLIND"
    assert evaluator_before["photo_id"] == "RIGHT_001"
    assert evaluator_before["evaluator_only"] is True

    minimal, minimal_zip = (
        build_real_house_5_p2_blind_package(
            package_id=PACKAGE_ID,
            prompt_variant="minimal",
        ),
        None,
    )
    master = build_real_house_5_p2_blind_package(
        package_id=PACKAGE_ID,
        prompt_variant="master",
    )

    with ZipFile(BytesIO(minimal.zip_bytes), "r") as left, ZipFile(
        BytesIO(master.zip_bytes), "r"
    ) as right:
        left_manifest = json.loads(left.read("manifest.json"))
        right_manifest = json.loads(right.read("manifest.json"))
        for key in (
            "schema_version",
            "project_id",
            "agent_id",
            "agent_display_name",
            "round_id",
            "package_id",
            "prompt_path",
            "photos",
        ):
            assert left_manifest[key] == right_manifest[key]
        assert left.read("photos/RIGHT_001.jpg") == right.read("photos/RIGHT_001.jpg")
        assert left.read("prompt.txt") != right.read("prompt.txt")


def test_master_blind_package_contains_no_evaluator_truth_payload() -> None:
    _, archive = _master_package()
    with archive:
        manifest = json.loads(archive.read("manifest.json"))
        searchable = b"\n".join(
            name.encode("utf-8") + b"\n" + archive.read(name)
            for name in archive.namelist()
        ).decode("utf-8", errors="ignore").casefold()

    for marker in PACKAGE_TRUTH_LEAK_MARKERS:
        assert marker.casefold() not in searchable

    # The benchmark name is intentionally present only as technical manifest identity.
    assert manifest["project_id"] == "REAL-HOUSE-5-P2-BLIND"

    # human_facts and its provenance field names are required generic V1
    # instructions; no concrete human-fact record or evaluator truth may leak.
    assert "hf001" not in searchable
    assert '"human_fact_id":' not in searchable
    assert '"fact_text":' not in searchable
