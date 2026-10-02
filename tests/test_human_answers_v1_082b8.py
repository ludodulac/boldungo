import json
from pathlib import Path
import subprocess

from brickhouse.exchange_v1 import validate_exchange_v1


ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
FIXTURES = ROOT / "tests" / "fixtures" / "exchange_v1"


def read(name: str) -> str:
    return (FRONTEND / name).read_text(encoding="utf-8")


def test_human_answers_runtime_contract(tmp_path: Path) -> None:
    output = tmp_path / "answers.json"
    completed = subprocess.run(
        ["node", "tests/human_answers_v1_082b8.mjs", str(output)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "BOLDUNGO-082B8 HUMAN_ANSWERS contract passed" in completed.stdout

    document = json.loads(output.read_text(encoding="utf-8"))
    source = json.loads((FIXTURES / "analysis_result_valid.json").read_text(encoding="utf-8"))
    validation = validate_exchange_v1(document, source_analysis_result=source)
    assert validation == {"status": "VALID HUMAN_ANSWERS", "reason": None}


def test_answers_use_indexeddb_project_storage() -> None:
    store = read("project-photo-store.js")
    answers = read("human-answers-v1.js")

    assert "analysis_answer_drafts: []" in store
    assert "export async function upsertAnalysisAnswerDraft" in store
    assert "database.transaction(STORE_PROJECTS, 'readwrite')" in store
    assert "analysis_answer_drafts:" in store
    assert "localStorage" not in answers
    assert "localStorage" not in store[store.index("upsertAnalysisAnswerDraftToProjectRecord"):]


def test_answer_ui_registered_after_result_renderer() -> None:
    package = read("brickhouse-survey-package.js")
    renderer_pos = package.index("analysis-result-render-v1.js")
    answers_pos = package.index("human-answers-v1.js")
    assert renderer_pos >= 0
    assert answers_pos > renderer_pos

    renderer = read("analysis-result-render-v1.js")
    answers = read("human-answers-v1.js")
    assert "boldungo:analysis-result-v1-rendered" in renderer
    assert "boldungo:analysis-result-v1-rendered" in answers
    assert "Télécharger mes réponses pour Sophie" in answers


def test_no_r002_or_ai_call_added() -> None:
    answers = read("human-answers-v1.js")
    assert "R002" not in answers
    assert "fetch(" not in answers
    assert "XMLHttpRequest" not in answers
    assert "INITIAL_SOPHIE_PROMPT" not in answers
    assert "HUMAN_ANSWERS" in answers
    assert "ANALYSIS_RESULT" in answers


def test_ui_contract_contains_required_answer_types_without_note_field() -> None:
    answers = read("human-answers-v1.js")
    assert "'Oui', 'YES'" in answers
    assert "'Non', 'NO'" in answers
    assert "question.choices" in answers
    assert "input.type = 'text'" in answers
    assert "Je ne sais pas" in answers
    assert "note: null" in answers


def test_export_filename_contract() -> None:
    answers = read("human-answers-v1.js")
    assert "BOLDUNGO_${result.project_id}_${result.agent_id}_${result.round_id}_ANSWERS.json" in answers
