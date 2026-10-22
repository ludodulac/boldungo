from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "frontend" / "instructions.html").read_text(encoding="utf-8")
JS = (ROOT / "frontend" / "instructions.js").read_text(encoding="utf-8")
CSS = (ROOT / "frontend" / "instructions.css").read_text(encoding="utf-8")


def test_order_area_is_after_notice_steps_and_becomes_visible_for_loaded_bundle():
    assert HTML.index('id="steps"') < HTML.index('id="order-section"')
    assert "Commander mes pièces" in HTML
    assert "orderSection.hidden=false" in JS
    assert "loadOrderOptions(b)" in JS


def test_order_totals_are_rendered_from_backend_user_order_options():
    assert "data.total_parts.toLocaleString('fr-FR')" in JS
    assert "data.total_bags" in JS
    assert "option.total_parts.toLocaleString('fr-FR')" in JS
    assert "option.total_bags" in JS
    assert "body:JSON.stringify({bundle})" in JS


def test_two_human_supplier_cards_and_readiness_states_are_present():
    assert "LEGO via BrickLink" in JS
    assert "Pièces LEGO originales" in JS
    assert "Briques compatibles" in JS
    assert "Commander via Wobrick" in JS
    assert "Commande prête" in JS
    assert "Dossier de commande prêt" in JS
    assert "Disponibilité vérifiée chez le fournisseur" in JS
    assert "La disponibilité sera vérifiée chez le fournisseur" in JS
    assert "Commande à finaliser" in JS


def test_backend_blocker_messages_are_reused_without_code_translation_table():
    assert "item.textContent=blocker.message" in JS
    assert "blocker.code===" not in JS


def test_document_ready_route_uses_backend_zip_endpoint_and_blocked_button_is_disabled():
    assert "/api/v1/prepare-order/${route}" in JS
    assert "action.disabled=!option.document_ready" in JS
    assert "await response.blob()" in JS
    assert "blob.size" in JS
    assert "new Zip" not in JS


def test_procurement_ui_does_not_expose_internal_format_jargon():
    visible = HTML + "\n".join(
        line for line in JS.splitlines()
        if "textContent=" in line or "ORDER_COPY=" in line
    )
    for jargon in (
        "CanonicalOrderPackage",
        "SupplierHandoffPackage",
        "crosswalk",
        "BagPlan",
        "physical requirement",
        "LDraw",
        "Rebrickable",
    ):
        assert jargon not in visible


def test_order_cards_are_mobile_first_without_desktop_width_dependency():
    assert ".order-options { display:grid; grid-template-columns:1fr;" in CSS
    assert "@media (max-width:700px)" in CSS
    assert ".order-main-action, .order-action { width:100%; min-height:52px;" in CSS
    assert "grid-template-columns:1fr 1fr" in CSS
