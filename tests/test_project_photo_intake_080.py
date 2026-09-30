from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"


def read(name: str) -> str:
    return (FRONTEND / name).read_text(encoding="utf-8")


def test_project_schema_v1_uses_indexeddb_for_binary_photo_records() -> None:
    store = read("project-photo-store.js")
    assert "PROJECT_SCHEMA_VERSION = 1" in store
    assert "indexedDB.open" in store
    assert "const STORE_PROJECTS = 'projects'" in store
    assert "const LEGACY_STORE_PHOTOS = 'photos'" in store
    assert "const STORE_PHOTOS = 'photos_v2'" in store
    assert "keyPath: ['project_id', 'photo_id']" in store
    assert "const STORE_SETTINGS = 'settings'" in store
    assert "blob: file" in store
    assert "localStorage" not in store
    assert "clarifications: []" in store
    assert "human_facts: []" in store


def test_canonical_photo_ids_are_monotonic_and_not_reassigned_on_delete() -> None:
    store = read("project-photo-store.js")
    assert "photo_id_counters" in store
    assert "counters[counterKey] += 1" in store
    assert "padStart(3, '0')" in store
    assert "const prefix = normalizedFace ? FACE_PREFIX[normalizedFace] : 'DETAIL'" in store
    delete_body = store.split("export async function deleteProjectPhoto", 1)[1].split(
        "export async function updateGroupNote", 1
    )[0]
    assert "photoStore.delete([projectId, photoId])" in delete_body
    assert "photo_id_counters" not in delete_body


def test_photo_page_exposes_project_city_privacy_and_three_quarter_policy() -> None:
    html = read("photo.html")
    assert 'id="project-picker"' in html
    assert 'id="new-project"' in html
    assert 'id="project-name"' in html
    assert 'id="city"' in html
    assert "Ville de la maison — facultatif" in html
    assert "La ville peut aider l’analyse à poser de meilleures questions" in html
    assert "conservées localement dans ce navigateur sur cet appareil" in html
    assert "ne sont pas envoyées à BOLDÜNGO simplement parce qu’elles sont enregistrées ici" in html
    assert "vue de trois-quarts" in html
    assert "PRIMARY_FACE" in html
    assert 'id="project-save-status"' in html


def test_capture_runtime_restores_persisted_photos_without_repopulating_file_inputs() -> None:
    runtime = read("photo-capture-runtime.js")
    assert "getActiveProjectSnapshot" in runtime
    assert "renderPersistedSlot" in runtime
    assert "persisted-photo-preview" in runtime
    assert "deleteProjectPhoto" in runtime
    assert "MAX_PHOTOS_PER_GROUP" in runtime
    assert "Enregistré sur cet appareil" in runtime
    assert "Erreur de sauvegarde" in runtime
    assert ".files =" in runtime
    assert "guided-photo-input" in runtime
    assert "input.files =" not in runtime


def test_pdf_handoff_prefers_indexeddb_project_and_emits_canonical_metadata() -> None:
    pdf = read("brickhouse-survey-hybrid-pdf.js")
    assert "getActiveProjectSnapshot" in pdf
    assert "photoRecordToFile" in pdf
    assert "indexeddb_project" in pdf
    assert "photo_id=" in pdf
    assert "PRIMARY_FACE=" in pdf
    assert "CITY = CONTEXTUAL_PRIOR" in pdf
    assert "CITY != ARCHITECTURAL_EVIDENCE" in pdf
    assert "project?.general_notes" in pdf


def test_080_browser_proof_is_wired_into_existing_ci_instead_of_parallel_infra() -> None:
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "python tests/browser_project_photo_intake_080.py" in workflow
    assert "node --check frontend/project-photo-store.js" in workflow


def test_project_creation_requires_explicit_name_and_no_automatic_ma_maison_project() -> None:
    store = read("project-photo-store.js")
    runtime = read("photo-capture-runtime.js")
    html = read("photo.html")
    assert "Nom du projet requis" in store
    assert "return null;" in store
    assert "return createProject();" not in store
    assert "createProject('Ma maison')" not in runtime
    assert 'id="project-create-panel"' in html
    assert 'id="new-project-name"' in html
    assert 'id="confirm-new-project"' in html
    assert "showProjectCreation('first')" in runtime
    assert "showProjectCreation('additional')" in runtime
    assert "cancelNewProject" in runtime


def test_project_rename_refreshes_selector_without_repopulating_name_field() -> None:
    runtime = read("photo-capture-runtime.js")
    rename_start = runtime.index("projectName?.addEventListener('input'")
    rename_end = runtime.index("bindProjectField(city", rename_start)
    rename_block = runtime[rename_start:rename_end]
    assert "updateProject" in rename_block
    assert "refreshProjectPicker" in rename_block
    assert "populateFields" not in rename_block
    assert "|| 'Ma maison'" not in rename_block


def test_legacy_auto_project_requires_naming_without_losing_existing_record() -> None:
    store = read("project-photo-store.js")
    runtime = read("photo-capture-runtime.js")
    assert "name_confirmed: true" in store
    assert "activeProject.name_confirmed === true" in runtime
    assert "showProjectCreation('legacy')" in runtime
    assert "projectCreationMode === 'legacy'" in runtime
    assert "name_confirmed: true" in runtime


def test_benchmark_fixture_context_is_separate_from_user_project_creation() -> None:
    loader = read("real-house-benchmark-loader.js")
    runtime = read("photo-capture-runtime.js")
    assert "waitForProjectIntakeReady" in loader
    assert "enableBenchmarkFixtureInputs" in loader
    assert "benchmarkFixtureContext" in loader
    assert "USER_PROJECT_CREATION" in loader
    assert "createProject(" not in loader
    assert "createProject('Ma maison')" not in runtime


def test_debounced_metadata_and_group_notes_capture_values_before_ui_reload() -> None:
    runtime = read("photo-capture-runtime.js")

    project_field_start = runtime.index("function bindProjectField")
    project_field_end = runtime.index("function bindProjectControls", project_field_start)
    project_field_block = runtime[project_field_start:project_field_end]
    assert "const candidate = element.value;" in project_field_block
    assert "[field]: normalize(candidate)" in project_field_block
    assert "normalize(element.value)" not in project_field_block

    photo_slot_start = runtime.index("function bindPhotoSlot")
    photo_slot_end = runtime.index("function bindProjectField", photo_slot_start)
    photo_slot_block = runtime[photo_slot_start:photo_slot_end]
    assert "const candidate = note.value;" in photo_slot_block
    assert "updateGroupNote(activeProject.project_id, key, candidate)" in photo_slot_block
    assert "updateGroupNote(activeProject.project_id, key, note.value)" not in photo_slot_block


def test_persisted_photo_consumes_transient_file_selection_and_preview_state() -> None:
    runtime = read("photo-capture-runtime.js")

    helper_start = runtime.index("function consumeTransientPhotoSelection")
    helper_end = runtime.index("function clearPreviewUrls", helper_start)
    helper_block = runtime[helper_start:helper_end]
    assert "input.value = '';" in helper_block
    assert "selected-photo-previews" in helper_block
    assert "transientPreviews.replaceChildren()" in helper_block
    assert "transientPreviews.dataset.count = '0'" in helper_block
    assert "syncTechnicalPhotoInput();" in helper_block

    add_start = runtime.index("async function addFilesFromSlot")
    add_end = runtime.index("function bindPhotoSlot", add_start)
    add_block = runtime[add_start:add_end]
    assert "if (!activeProject) return;" in add_block
    assert "await addPhotosToProject" in add_block
    assert "consumeTransientPhotoSelection(slot, input);" in add_block
    assert add_block.index("await addPhotosToProject") < add_block.index("consumeTransientPhotoSelection(slot, input);")
    assert add_block.index("consumeTransientPhotoSelection(slot, input);") < add_block.index("await reloadActiveProject();")
