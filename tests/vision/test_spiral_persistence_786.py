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
    import_spatial_pixel_check_response,
    record_assertion_revision,
    record_spatial_organization_state,
    SpatialOrganizationAssertion,
    SpatialOrganizationCandidate,
    SpatialViewPrediction,
    ViewExplanationGain,
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


def test_787_candidate_organization_predictions_and_gain_survive_reload():
    workspace = _workspace_062()
    workspace = _reject(workspace, "obs_p2_stair", "spiral-persistence-786:obs_p2_stair",
                        "Public photo 02 does not visibly contain the exterior stair described by 062.")
    workspace = _reject(workspace, "obs_p2_box_volume", "spiral-persistence-786:obs_p2_box_volume",
                        "Public photo 02 does not visibly contain the pale projecting box volume described by 062.")

    observations = {x.id: x for x in [*workspace.pass_1.observations, *workspace.pass_2.observations]}
    def prov(ref):
        o=observations[ref]
        return RichEvidenceProvenance(observation_ref=ref,photo_index=o.photo_index,
                                      roi=(o.region.x0,o.region.y0,o.region.x1,o.region.y1))

    organization = SpatialOrganizationCandidate(
        organization_id="org_rear_sector_787", sector_label="bounded rear/side sector P3-P5",
        observation_refs=["obs_p3_box_volume","obs_p3_dark_opening","obs_p4_rear_wall","obs_p4_terrace","obs_p4_stair","obs_p5_side_wall"],
        assertions=[
            SpatialOrganizationAssertion(assertion_id="org787-a1",subject_ref="rear_side_wall_sector",relation_token="COEXISTS_IN_SECTOR",object_ref="lower_clear_volume",epistemic_level="CANDIDATE",source_observation_refs=["obs_p3_box_volume","obs_p4_rear_wall"]),
            SpatialOrganizationAssertion(assertion_id="org787-a2",subject_ref="raised_timber_platform",relation_token="COEXISTS_IN_SECTOR",object_ref="exterior_stair",epistemic_level="CANDIDATE",source_observation_refs=["obs_p4_terrace","obs_p4_stair"]),
        ],
        unresolved=["physical identity across P3/P4/P5 remains candidate","exact attachment/contact topology UNKNOWN","metric geometry UNKNOWN"],
    )
    predictions=[
        SpatialViewPrediction(prediction_id="pred787-p3",organization_ref=organization.organization_id,photo_index=3,
            observation_refs=["obs_p3_box_volume","obs_p3_dark_opening"],
            expected_observable_consequence="The wider P3 sector can show the clear lower volume and its large dark opening as part of the bounded sector; platform/stair continuity beyond the encoded 062 observations remains unresolved.",
            inspection_provenance=[prov("obs_p3_box_volume"),prov("obs_p3_dark_opening")],verification_state="AMBIGUOUS",
            verification_evidence="785 visually supports a wider rear-side ensemble, but 062 has no independent P3 stair/deck observations to make the cross-view organization acquired truth.",
            verification_provenance=[prov("obs_p3_box_volume"),prov("obs_p3_dark_opening")],observer_investigation_id="first-spatial-spiral-p2-p5"),
        SpatialViewPrediction(prediction_id="pred787-p4",organization_ref=organization.organization_id,photo_index=4,
            observation_refs=["obs_p4_rear_wall","obs_p4_terrace","obs_p4_stair"],
            expected_observable_consequence="P4 should simultaneously expose pale wall, raised timber platform and exterior stair in the same bounded sector.",
            inspection_provenance=[prov("obs_p4_rear_wall"),prov("obs_p4_terrace"),prov("obs_p4_stair")],verification_state="SUPPORTED",
            verification_evidence="The accepted 062 observations independently record all three visible elements in photo 4; 785 also retained this coexistence.",
            verification_provenance=[prov("obs_p4_rear_wall"),prov("obs_p4_terrace"),prov("obs_p4_stair")],observer_investigation_id="first-spatial-spiral-p2-p5"),
        SpatialViewPrediction(prediction_id="pred787-p5",organization_ref=organization.organization_id,photo_index=5,
            observation_refs=["obs_p5_side_wall"],
            expected_observable_consequence="P5 should expose the pale wall sector; the stronger stair/box/deck relative arrangement from 785 remains candidate rather than promoted from prose.",
            inspection_provenance=[prov("obs_p5_side_wall")],verification_state="AMBIGUOUS",
            verification_evidence="P5 wall evidence is persisted, but the 062 workspace lacks separate P5 stair/box/deck observations needed to verify the full organization without a new observer import.",
            verification_provenance=[prov("obs_p5_side_wall")],observer_investigation_id="first-spatial-spiral-p2-p5"),
        SpatialViewPrediction(prediction_id="pred787-p2-control",organization_ref=organization.organization_id,photo_index=2,
            observation_refs=[],expected_observable_consequence="The bounded P3-P5 organization does not require the stair or lower clear volume to be observable in P2.",
            inspection_provenance=[],verification_state="NOT_OBSERVABLE",
            verification_evidence="P2 is a negative/non-required control. Absence of a required prediction is not a contradiction; the two former P2 claims are separately rejected by persistent revisions.",
            verification_provenance=[],observer_investigation_id="spiral-persistence-786"),
    ]
    gain=ViewExplanationGain(organization_ref=organization.organization_id,
        constrained_photo_indexes_before=[3,4,5],constrained_photo_indexes_after=[3,4,5],
        linked_observation_refs_before=[],linked_observation_refs_after=organization.observation_refs,
        supported_prediction_ids=["pred787-p4"],contradicted_prediction_ids=[],
        ambiguous_prediction_ids=["pred787-p3","pred787-p5"],not_observable_prediction_ids=["pred787-p2-control"],
        remaining_ambiguities=organization.unresolved,invented_geometry_added=False)
    loaded=MultiViewWorkspace.model_validate_json(workspace.model_copy(update={
        "spatial_organizations":[organization],"spatial_view_predictions":predictions,"view_explanation_gains":[gain]
    }).model_dump_json())
    assert len(loaded.spatial_organizations)==1
    assert {p.verification_state.value for p in loaded.spatial_view_predictions}=={"SUPPORTED","AMBIGUOUS","NOT_OBSERVABLE"}
    assert loaded.view_explanation_gains[0].invented_geometry_added is False
    assert loaded.view_explanation_gains[0].contradicted_prediction_ids == []
    assert "obs_p2_stair" not in loaded.spatial_organizations[0].observation_refs
    assert "obs_p2_box_volume" not in loaded.spatial_organizations[0].observation_refs


def test_789_response_788_import_revision_gain_and_pixel_provenance_survive_reload():
    workspace = _workspace_062()
    workspace = _reject(workspace, "obs_p2_stair", "spiral-persistence-786:obs_p2_stair",
                        "Public photo 02 does not visibly contain the exterior stair described by 062.")
    workspace = _reject(workspace, "obs_p2_box_volume", "spiral-persistence-786:obs_p2_box_volume",
                        "Public photo 02 does not visibly contain the pale projecting box volume described by 062.")
    organization = SpatialOrganizationCandidate(
        organization_id="org_rear_sector_787", sector_label="bounded rear/side sector P3-P5",
        observation_refs=["obs_p3_box_volume","obs_p3_dark_opening","obs_p4_rear_wall","obs_p4_terrace","obs_p4_stair","obs_p5_side_wall"],
        assertions=[
            SpatialOrganizationAssertion(assertion_id="org787-a1",subject_ref="rear_side_wall_sector",relation_token="COEXISTS_IN_SECTOR",object_ref="lower_clear_volume",epistemic_level="CANDIDATE",source_observation_refs=["obs_p3_box_volume","obs_p4_rear_wall"]),
            SpatialOrganizationAssertion(assertion_id="org787-a2",subject_ref="raised_timber_platform",relation_token="COEXISTS_IN_SECTOR",object_ref="exterior_stair",epistemic_level="CANDIDATE",source_observation_refs=["obs_p4_terrace","obs_p4_stair"]),
        ],
        unresolved=["physical identity across P3/P4/P5 remains candidate","exact attachment/contact topology UNKNOWN","metric geometry UNKNOWN"],
    )
    baseline_gain = ViewExplanationGain(
        organization_ref=organization.organization_id,
        constrained_photo_indexes_before=[3,4,5], constrained_photo_indexes_after=[3,4,5],
        linked_observation_refs_before=[], linked_observation_refs_after=organization.observation_refs,
        supported_prediction_ids=[], contradicted_prediction_ids=[],
        ambiguous_prediction_ids=[], not_observable_prediction_ids=[],
        remaining_ambiguities=organization.unresolved, invented_geometry_added=False,
    )
    workspace = MultiViewWorkspace.model_validate(workspace.model_copy(update={
        "spatial_organizations":[organization], "view_explanation_gains":[baseline_gain]
    }).model_dump())

    root = Path(__file__).parents[2]
    request = __import__("json").loads((root / "frontend" / "spatial-pixel-check-request-788.json").read_text())
    response = __import__("json").loads((root / "frontend" / "spatial-pixel-check-response-788.json").read_text())
    workspace = import_spatial_pixel_check_response(workspace, request, response)

    imported = {p.prediction_id:p for p in workspace.spatial_view_predictions if p.observer_investigation_id=="spatial-pixel-check-788"}
    assert set(imported) == {t["test_id"] for t in request["spatial_tests"]}
    assert imported["788-p3-volume-opening"].verification_relation_tokens == ["CONTAINED_WITHIN"]
    assert imported["788-p4-left-right-order"].verification_relation_tokens == ["LEFT_OF","BELOW"]
    assert imported["788-p5-sector-structure"].verification_relation_tokens == ["LEFT_OF","BELOW","BOUNDARY_JOINS"]
    assert imported["788-p4-stair-platform"].verification_state.value == "NOT_OBSERVABLE"
    assert imported["788-p4-wall-platform"].verification_state.value == "AMBIGUOUS"
    assert all(p.verification_provenance and all(q.pixel_cues for q in p.verification_provenance) for p in imported.values())

    revised = organization.model_copy(update={
        "assertions":[
            *organization.assertions,
            SpatialOrganizationAssertion(assertion_id="org789-p3-contained",subject_ref="dark_opening",relation_token="CONTAINED_WITHIN",object_ref="lower_clear_volume",epistemic_level="CANDIDATE",source_observation_refs=["obs_p3_box_volume","obs_p3_dark_opening"]),
            SpatialOrganizationAssertion(assertion_id="org789-p4-left",subject_ref="exterior_stair",relation_token="LEFT_OF",object_ref="platform_wall_sector",epistemic_level="CANDIDATE",source_observation_refs=["obs_p4_stair","obs_p4_terrace","obs_p4_rear_wall"]),
            SpatialOrganizationAssertion(assertion_id="org789-p4-below",subject_ref="exterior_stair",relation_token="BELOW",object_ref="platform_wall_sector",epistemic_level="CANDIDATE",source_observation_refs=["obs_p4_stair","obs_p4_terrace","obs_p4_rear_wall"]),
            SpatialOrganizationAssertion(assertion_id="org789-p5-left",subject_ref="p5_stair_diagonal_sector",relation_token="LEFT_OF",object_ref="p5_platform_sector",epistemic_level="CANDIDATE",source_observation_refs=["obs_p5_side_wall"]),
            SpatialOrganizationAssertion(assertion_id="org789-p5-below",subject_ref="p5_stair_diagonal_sector",relation_token="BELOW",object_ref="p5_platform_sector",epistemic_level="CANDIDATE",source_observation_refs=["obs_p5_side_wall"]),
            SpatialOrganizationAssertion(assertion_id="org789-p5-joins",subject_ref="p5_stair_diagonal_sector",relation_token="BOUNDARY_JOINS",object_ref="p5_platform_sector",epistemic_level="CANDIDATE",source_observation_refs=["obs_p5_side_wall"]),
        ],
        "unresolved":[
            "physical identity across P3/P4/P5 remains candidate",
            "P4 stair-platform raccord NOT_OBSERVABLE",
            "P4 wall-platform relation AMBIGUOUS",
            "P3 lower-volume/adjacent-wall precise junction AMBIGUOUS",
            "metric geometry UNKNOWN",
        ],
    })
    gain = ViewExplanationGain(
        organization_ref=organization.organization_id,
        constrained_photo_indexes_before=[3,4,5], constrained_photo_indexes_after=[3,4,5],
        linked_observation_refs_before=organization.observation_refs, linked_observation_refs_after=organization.observation_refs,
        supported_prediction_ids=["788-p3-volume-opening","788-p4-left-right-order","788-p5-sector-structure"],
        contradicted_prediction_ids=[],
        ambiguous_prediction_ids=["788-p3-visible-junctions","788-p4-wall-platform"],
        not_observable_prediction_ids=["788-p4-stair-platform"],
        remaining_ambiguities=revised.unresolved, invented_geometry_added=False,
    )
    workspace = record_spatial_organization_state(workspace, revised, gain)

    saved = workspace.model_dump_json()
    loaded = MultiViewWorkspace.model_validate_json(saved)
    imported_after = {p.prediction_id:p for p in loaded.spatial_view_predictions if p.observer_investigation_id=="spatial-pixel-check-788"}
    assert len(imported_after) == 6
    assert imported_after["788-p5-sector-structure"].verification_relation_tokens == ["LEFT_OF","BELOW","BOUNDARY_JOINS"]
    assert all(q.pixel_cues for p in imported_after.values() for q in p.verification_provenance)
    assert {a.relation_token for a in loaded.spatial_organizations[0].assertions} >= {"CONTAINED_WITHIN","LEFT_OF","BELOW","BOUNDARY_JOINS"}
    loaded_gain = loaded.view_explanation_gains[0]
    assert loaded_gain.supported_prediction_ids == ["788-p3-volume-opening","788-p4-left-right-order","788-p5-sector-structure"]
    assert loaded_gain.ambiguous_prediction_ids == ["788-p3-visible-junctions","788-p4-wall-platform"]
    assert loaded_gain.not_observable_prediction_ids == ["788-p4-stair-platform"]
    assert loaded_gain.contradicted_prediction_ids == []
    assert loaded_gain.invented_geometry_added is False
    assert "metric geometry UNKNOWN" in loaded_gain.remaining_ambiguities
