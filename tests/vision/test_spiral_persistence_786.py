from pathlib import Path

from brickhouse.vision.multiview import (
    AssertionRevision,
    ClaimStatus,
    MultiViewWorkspace,
    RichEvidenceProvenance,
    RichVisualBootstrapResponse,
    assess_assertion_revision_impacts,
    build_multiview_world_constraint_graph,
    build_rich_multiview_bootstrap_request,
    build_world_hypothesis,
    import_rich_visual_bootstrap_response,
    invalidated_observation_ids,
    record_assertion_revision,
)


def _workspace_062() -> MultiViewWorkspace:
    fixture_dir = Path(__file__).parents[1] / "fixtures" / "vision"
    response = RichVisualBootstrapResponse.model_validate_json(
        (fixture_dir / "visual-bootstrap-response-062.json").read_text()
    )
    request = build_rich_multiview_bootstrap_request(
        "real-house-5-rich-multiview-062",
        ["01-original.jpg", "02-original.jpg", "03-original.jpg", "04-original.jpg", "05-original.jpg"],
    )
    return import_rich_visual_bootstrap_response(request, response)


def _reject(workspace: MultiViewWorkspace, observation_ref: str, revision_id: str, reason: str) -> MultiViewWorkspace:
    observations = {x.id: x for x in [*workspace.pass_1.observations, *workspace.pass_2.observations]}
    observation = observations[observation_ref]
    assert observation.region is not None
    provenance = RichEvidenceProvenance(
        observation_ref=observation.id,
        photo_index=observation.photo_index,
        roi=(observation.region.x0, observation.region.y0, observation.region.x1, observation.region.y1),
    )
    return record_assertion_revision(
        workspace,
        AssertionRevision(
            revision_id=revision_id,
            assertion_ref=observation_ref,
            previous_status=observation.status.value,
            new_epistemic_state="REJECTED_BY_PIXELS",
            reason=reason,
            provenance=[provenance],
        ),
    )


def test_786_real_785_corrections_survive_reload_and_stop_active_support():
    workspace = _workspace_062()
    workspace = _reject(
        workspace,
        "obs_p2_stair",
        "spiral-persistence-786:obs_p2_stair",
        "Public photo 02 does not visibly contain the exterior stair described by 062; the inspected ROI is wall/street-side content.",
    )
    workspace = _reject(
        workspace,
        "obs_p2_box_volume",
        "spiral-persistence-786:obs_p2_box_volume",
        "Public photo 02 does not visibly contain the pale projecting box volume described by 062.",
    )

    # Conversation A saves; Conversation B knows only the persisted artifact.
    saved = workspace.model_dump_json()
    loaded = MultiViewWorkspace.model_validate_json(saved)

    historical = {x.id: x for x in [*loaded.pass_1.observations, *loaded.pass_2.observations]}
    assert historical["obs_p2_stair"].status is ClaimStatus.OBSERVED
    assert historical["obs_p2_box_volume"].status is ClaimStatus.OBSERVED
    assert invalidated_observation_ids(loaded) == {"obs_p2_stair", "obs_p2_box_volume"}
    assert {x.assertion_ref for x in loaded.assertion_revisions} == {"obs_p2_stair", "obs_p2_box_volume"}
    assert all(x.provenance and x.provenance[0].photo_index == 2 for x in loaded.assertion_revisions)

    stair_impacts = assess_assertion_revision_impacts(loaded, "obs_p2_stair")
    box_impacts = assess_assertion_revision_impacts(loaded, "obs_p2_box_volume")
    assert any(x.affected_kind == "identity_candidate" and x.affected_ref == "idc_stair_p2_p4" for x in stair_impacts)
    assert any(x.affected_kind == "identity_cue" and x.disposition == "NEEDS_REEVALUATION" for x in stair_impacts)
    assert any(x.affected_kind == "identity_candidate" and x.affected_ref == "idc_box_p2_p3" for x in box_impacts)
    assert any(x.affected_kind == "identity_cue" and x.disposition == "NEEDS_REEVALUATION" for x in box_impacts)

    graph = build_multiview_world_constraint_graph(loaded)
    graph_refs = {node.source_ref for node in graph.nodes}
    assert "obs_p2_stair" not in graph_refs
    assert "obs_p2_box_volume" not in graph_refs
    assert "idc_stair_p2_p4" not in graph_refs
    assert "idc_box_p2_p3" not in graph_refs
    assert all(
        p.observation_ref not in {"obs_p2_stair", "obs_p2_box_volume"}
        for constraint in graph.constraints
        for p in constraint.provenance
    )

    hypothesis = build_world_hypothesis(loaded, graph)
    assert "idc_stair_p2_p4" not in hypothesis.identity_candidate_refs
    assert "idc_box_p2_p3" not in hypothesis.identity_candidate_refs
    assert all(
        ref not in {"obs_p2_stair", "obs_p2_box_volume"}
        for organization in hypothesis.organizations
        for ref in [*organization.main_world_observation_refs, *organization.unattached_observation_refs]
    )
    assert all(
        p.observation_ref not in {"obs_p2_stair", "obs_p2_box_volume"}
        for organization in hypothesis.organizations
        for assertion in organization.assertions
        for p in assertion.provenance
    )
