import hashlib
import json
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

from brickhouse.blind_benchmark_v1 import build_real_house_5_p2_blind_package
from brickhouse.exchange_v1 import (
    Entity,
    HumanFact,
    Observation,
    Question,
    Relation,
    Uncertainty,
    validate_exchange_v1,
)


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


def _assert_exact_required_fields(prompt: str, heading: str, model) -> None:
    marker = f"{heading} — CHAMPS OBLIGATOIRES EXACTS\n"
    start = prompt.index(marker) + len(marker)
    lines = prompt[start:].splitlines()
    declared = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            break
        if stripped in model.model_fields:
            declared.append(stripped)
        else:
            break
    assert declared == list(model.model_fields)


def test_083f_master_prompt_declares_exact_backend_object_fields() -> None:
    prompt = _master_prompt_from_package()

    _assert_exact_required_fields(prompt, "OBSERVATION", Observation)
    _assert_exact_required_fields(prompt, "HUMAN_FACT", HumanFact)
    _assert_exact_required_fields(prompt, "ENTITY", Entity)
    _assert_exact_required_fields(prompt, "RELATION", Relation)
    _assert_exact_required_fields(prompt, "UNCERTAINTY", Uncertainty)
    _assert_exact_required_fields(prompt, "QUESTION", Question)


def test_083f_master_prompt_forbids_first_blind_run_aliases() -> None:
    prompt = _master_prompt_from_package()

    required_bans = (
        'N’utilise jamais un champ générique "id"',
        'Dans une observation, "id" est interdit ; utilise observation_id.',
        'Dans une observation, "statement" est interdit ; utilise observation_text.',
        'Dans une entity, "id" est interdit ; utilise entity_id.',
        'Dans une relation, "id" est interdit ; utilise relation_id.',
        '"from_entity_id", "to_entity_id", "from" et "to" sont interdits',
        'utilise exclusivement subject_entity_id et object_entity_id.',
        'Dans une uncertainty, "id" est interdit ; utilise uncertainty_id.',
        'Dans une question, "id" est interdit ; utilise question_id.',
        'Dans une question, "question" est interdit comme nom de champ ; utilise question_text.',
        "Tout champ supplémentaire non déclaré par le contrat est interdit.",
    )
    for marker in required_bans:
        assert marker in prompt


def test_083f_master_prompt_declares_exact_question_answer_contract() -> None:
    prompt = _master_prompt_from_package()

    for answer_type in ("YES_NO", "SINGLE_CHOICE", "FREE_TEXT"):
        assert answer_type in prompt

    assert 'Pour YES_NO :\nchoices = []' in prompt
    assert 'Pour FREE_TEXT :\nchoices = []' in prompt
    assert "Pour SINGLE_CHOICE :" in prompt
    assert "choices contient au moins deux objets ayant exactement :" in prompt
    assert "value est une chaîne ASCII non vide" in prompt
    assert "allow_unknown est un booléen obligatoire : true ou false" in prompt


def test_083f_master_prompt_declares_open_uncertainty_defaults() -> None:
    prompt = _master_prompt_from_package()

    expected = (
        'Pour une uncertainty nouvelle non résolue :\n'
        'resolution_state = "OPEN"\n'
        'resolved_by_human_fact_refs = []\n'
        'resolved_by_observation_refs = []'
    )
    assert expected in prompt


def test_083f_neutral_json_skeleton_is_valid_exchange_v1_analysis_result() -> None:
    prompt = _master_prompt_from_package()
    heading = "SQUELETTE JSON MINIMAL CONFORME"
    end_marker = "FIN DU SQUELETTE JSON MINIMAL"

    section = prompt[prompt.index(heading):prompt.index(end_marker)]
    json_start = section.index("{")
    skeleton = json.loads(section[json_start:])

    assert skeleton["payload"]["analysis"] == {
        "observations": [],
        "human_facts": [],
        "entities": [],
        "relations": [],
        "uncertainties": [],
    }
    assert skeleton["payload"]["questions"] == []
    assert validate_exchange_v1(skeleton) == {
        "status": "VALID ANALYSIS_RESULT",
        "reason": None,
    }


def test_083f_neutral_json_skeleton_contains_no_architectural_truth() -> None:
    prompt = _master_prompt_from_package()
    heading = "SQUELETTE JSON MINIMAL CONFORME"
    end_marker = "FIN DU SQUELETTE JSON MINIMAL"
    section = prompt[prompt.index(heading):prompt.index(end_marker)].casefold()

    for marker in PROMPT_BENCHMARK_LEAK_MARKERS:
        assert marker.casefold() not in section

def test_083i_master_prompt_preserves_open_voids_instead_of_inventing_closed_volume() -> None:
    prompt = _master_prompt_from_package()

    assert "VIDES / ESPACES OUVERTS / VOLUMES" in prompt
    assert "ne doit jamais être automatiquement interprété comme une ouverture pratiquée dans un volume fermé" in prompt
    assert "Avant de créer une entity VOLUME, exige des preuves positives" in prompt
    assert "Un vide visible ne doit jamais être rempli mentalement" in prompt


def test_083i_master_prompt_requires_demonstrated_host_before_opening() -> None:
    prompt = _master_prompt_from_package()

    assert "HOST TEST POUR UNE OPENING" in prompt
    assert "Une entity OPENING ne peut être créée que si son support physique" in prompt
    assert "rectangle sombre → OPENING → donc mur ou volume autour" in prompt
    assert "démontrer d’abord l’existence du mur, de la surface ou du volume hôte" in prompt
    assert "Si l’hôte n’est pas démontré" in prompt
    assert "ne crée pas d’entity OPENING" in prompt


def test_083i_master_prompt_treats_negative_space_as_architectural_evidence() -> None:
    prompt = _master_prompt_from_package()

    assert "NEGATIVE SPACE = PREUVE" in prompt
    assert "Les espaces vides visibles sont eux-mêmes de la preuve architecturale." in prompt
    assert "La continuité visuelle du sol derrière" in prompt
    assert "la lumière traversante" in prompt
    assert "un espace entre supports" in prompt
    assert "doivent peser contre l’hypothèse d’un volume fermé" in prompt


def test_083i_master_prompt_platform_does_not_imply_enclosed_volume() -> None:
    prompt = _master_prompt_from_package()

    assert "PLATEFORME / PALIER / STRUCTURE" in prompt
    assert "sans constituer un volume fermé" in prompt
    assert "SURFACE DE CIRCULATION\n≠\nSTRUCTURE PORTEUSE\n≠\nVOLUME FERMÉ" in prompt
    assert "Ne crée une entity VOLUME que si la fermeture physique est positivement démontrée." in prompt


def test_083i_master_prompt_side_walls_or_supports_do_not_imply_closure() -> None:
    prompt = _master_prompt_from_package()

    assert "parois latérales" in prompt
    assert "poteaux" in prompt
    assert "poutres" in prompt
    assert "ne suffit pas à démontrer que l’espace situé dessous est fermé" in prompt
    assert "Des parois latérales ou des supports ne prouvent pas la fermeture de l’espace." in prompt

def test_083k_master_prompt_separates_landing_surface_from_support_structure() -> None:
    prompt = _master_prompt_from_package()

    assert "PALIER / SURFACE DE CIRCULATION — DÉCOMPOSITION" in prompt
    assert "peut constituer un objet architectural distinct" in prompt
    assert "Ne fusionne pas automatiquement palier, muret ou parapet, support et volume" in prompt
    assert "représente-la séparément par une entity adaptée" in prompt
    assert "la surface de circulation, plateforme ou palier" in prompt
    assert "la structure porteuse éventuelle" in prompt
    assert "l’espace vide ou ouvert sous-jacent" in prompt


def test_083k_master_prompt_landing_may_exist_without_enclosed_volume_below() -> None:
    prompt = _master_prompt_from_package()

    assert "sans exiger qu’un volume fermé existe dessous" in prompt
    assert "La surface de circulation peut donc exister comme objet distinct" in prompt
    assert "même lorsque l’espace situé dessous reste ouvert" in prompt
    assert "un volume fermé seulement si sa fermeture physique est démontrée" in prompt


def test_083k_master_prompt_preserves_stair_to_landing_relation_when_evidenced() -> None:
    prompt = _master_prompt_from_package()

    assert "RELATIONS TOPOLOGIQUES DES PALIERS" in prompt
    assert "Un escalier CONNECTED_TO un palier doit être représenté" in prompt
    assert "si la connexion est visuellement soutenue" in prompt


def test_083k_master_prompt_preserves_landing_to_building_relation_when_evidenced() -> None:
    prompt = _master_prompt_from_package()

    assert "Un palier CONNECTED_TO le bâtiment doit être représenté" in prompt
    assert "si la jonction avec le bâtiment est visuellement soutenue" in prompt


def test_083k_master_prompt_hidden_connection_becomes_uncertainty_not_invented_relation() -> None:
    prompt = _master_prompt_from_package()

    assert "Ne déduis aucune de ces relations par simple proximité" in prompt
    assert "Si une connexion exacte est masquée ou non observable" in prompt
    assert "utilise une uncertainty plutôt que d’inventer une relation certaine" in prompt


def test_083k_master_prompt_keeps_all_083i_open_void_protections() -> None:
    prompt = _master_prompt_from_package()

    required_083i = (
        "VIDES / ESPACES OUVERTS / VOLUMES",
        "Avant de créer une entity VOLUME, exige des preuves positives",
        "HOST TEST POUR UNE OPENING",
        "Une entity OPENING ne peut être créée que si son support physique",
        "NEGATIVE SPACE = PREUVE",
        "Les espaces vides visibles sont eux-mêmes de la preuve architecturale.",
        "PLATEFORME / PALIER / STRUCTURE",
        "Des parois latérales ou des supports ne prouvent pas la fermeture de l’espace.",
        "La décomposition d’un palier ne prouve jamais un volume fermé sous celui-ci.",
        "Elle ne permet jamais de créer une OPENING sans host démontré.",
        "Elle ne permet jamais de fermer mentalement un vide visible",
    )
    for marker in required_083i:
        assert marker in prompt

