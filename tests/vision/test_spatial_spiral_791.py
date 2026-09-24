import json
from pathlib import Path
import pytest

from brickhouse.vision.multiview import (
    AssertionRevision, MultiViewWorkspace, RichEvidenceProvenance, RichVisualBootstrapResponse,
    SpatialOrganizationAssertion, SpatialOrganizationCandidate, ViewExplanationGain,
    build_rich_multiview_bootstrap_request, import_rich_visual_bootstrap_response,
    import_spatial_interview_discriminant_response, import_spatial_pixel_check_response,
    record_assertion_revision, record_spatial_organization_state,
    spatial_interview_discriminant_already_executed,
)

ROOT=Path(__file__).parents[2]
FIXTURES=ROOT/"tests"/"fixtures"/"vision"

def _workspace_789():
    response=RichVisualBootstrapResponse.model_validate_json((FIXTURES/"visual-bootstrap-response-062.json").read_text())
    request=build_rich_multiview_bootstrap_request("real-house-5-rich-multiview-062",
        ["01-original.jpg","02-original.jpg","03-original.jpg","04-original.jpg","05-original.jpg"])
    workspace=import_rich_visual_bootstrap_response(request,response)
    observations={x.id:x for x in [*workspace.pass_1.observations,*workspace.pass_2.observations]}
    for ref,rid,reason in [
        ("obs_p2_stair","spiral-persistence-786:obs_p2_stair","Public photo 02 does not visibly contain the exterior stair described by 062; the inspected ROI is wall/street-side content."),
        ("obs_p2_box_volume","spiral-persistence-786:obs_p2_box_volume","Public photo 02 does not visibly contain the pale projecting box volume described by 062.")]:
        o=observations[ref]
        workspace=record_assertion_revision(workspace,AssertionRevision(
            revision_id=rid,assertion_ref=ref,previous_status=o.status.value,new_epistemic_state="REJECTED_BY_PIXELS",
            reason=reason,provenance=[RichEvidenceProvenance(observation_ref=ref,photo_index=o.photo_index,
                roi=(o.region.x0,o.region.y0,o.region.x1,o.region.y1))]))
    organization=SpatialOrganizationCandidate(
        organization_id="org_rear_sector_787",sector_label="bounded rear/side sector P3-P5",
        observation_refs=["obs_p3_box_volume","obs_p3_dark_opening","obs_p4_rear_wall","obs_p4_terrace","obs_p4_stair","obs_p5_side_wall"],
        assertions=[
            SpatialOrganizationAssertion(assertion_id="org787-a1",subject_ref="rear_side_wall_sector",relation_token="COEXISTS_IN_SECTOR",object_ref="lower_clear_volume",epistemic_level="CANDIDATE",source_observation_refs=["obs_p3_box_volume","obs_p4_rear_wall"]),
            SpatialOrganizationAssertion(assertion_id="org787-a2",subject_ref="raised_timber_platform",relation_token="COEXISTS_IN_SECTOR",object_ref="exterior_stair",epistemic_level="CANDIDATE",source_observation_refs=["obs_p4_terrace","obs_p4_stair"]),
        ],
        unresolved=["physical identity across P3/P4/P5 remains candidate","exact attachment/contact topology UNKNOWN","metric geometry UNKNOWN"])
    gain=ViewExplanationGain(organization_ref=organization.organization_id,
        constrained_photo_indexes_before=[3,4,5],constrained_photo_indexes_after=[3,4,5],
        linked_observation_refs_before=[],linked_observation_refs_after=organization.observation_refs,
        remaining_ambiguities=organization.unresolved,invented_geometry_added=False)
    workspace=MultiViewWorkspace.model_validate(workspace.model_copy(update={
        "spatial_organizations":[organization],"view_explanation_gains":[gain]}).model_dump())
    request788=json.loads((ROOT/"frontend"/"spatial-pixel-check-request-788.json").read_text())
    response788=json.loads((ROOT/"frontend"/"spatial-pixel-check-response-788.json").read_text())
    workspace=import_spatial_pixel_check_response(workspace,request788,response788)
    revised=organization.model_copy(update={
        "assertions":[*organization.assertions,
            SpatialOrganizationAssertion(assertion_id="org789-p3-contained",subject_ref="dark_opening",relation_token="CONTAINED_WITHIN",object_ref="lower_clear_volume",epistemic_level="CANDIDATE",source_observation_refs=["obs_p3_box_volume","obs_p3_dark_opening"]),
            SpatialOrganizationAssertion(assertion_id="org789-p4-left",subject_ref="exterior_stair",relation_token="LEFT_OF",object_ref="platform_wall_sector",epistemic_level="CANDIDATE",source_observation_refs=["obs_p4_stair","obs_p4_terrace","obs_p4_rear_wall"]),
            SpatialOrganizationAssertion(assertion_id="org789-p4-below",subject_ref="exterior_stair",relation_token="BELOW",object_ref="platform_wall_sector",epistemic_level="CANDIDATE",source_observation_refs=["obs_p4_stair","obs_p4_terrace","obs_p4_rear_wall"]),
            SpatialOrganizationAssertion(assertion_id="org789-p5-left",subject_ref="p5_stair_diagonal_sector",relation_token="LEFT_OF",object_ref="p5_platform_sector",epistemic_level="CANDIDATE",source_observation_refs=["obs_p5_side_wall"]),
            SpatialOrganizationAssertion(assertion_id="org789-p5-below",subject_ref="p5_stair_diagonal_sector",relation_token="BELOW",object_ref="p5_platform_sector",epistemic_level="CANDIDATE",source_observation_refs=["obs_p5_side_wall"]),
            SpatialOrganizationAssertion(assertion_id="org789-p5-joins",subject_ref="p5_stair_diagonal_sector",relation_token="BOUNDARY_JOINS",object_ref="p5_platform_sector",epistemic_level="CANDIDATE",source_observation_refs=["obs_p5_side_wall"])],
        "unresolved":["physical identity across P3/P4/P5 remains candidate","P4 stair-platform raccord NOT_OBSERVABLE",
            "P4 wall-platform relation AMBIGUOUS","P3 lower-volume/adjacent-wall precise junction AMBIGUOUS","metric geometry UNKNOWN"]})
    gain=ViewExplanationGain(organization_ref=revised.organization_id,
        constrained_photo_indexes_before=[3,4,5],constrained_photo_indexes_after=[3,4,5],
        linked_observation_refs_before=revised.observation_refs,linked_observation_refs_after=revised.observation_refs,
        supported_prediction_ids=["788-p3-volume-opening","788-p4-left-right-order","788-p5-sector-structure"],
        contradicted_prediction_ids=[],ambiguous_prediction_ids=["788-p3-visible-junctions","788-p4-wall-platform"],
        not_observable_prediction_ids=["788-p4-stair-platform"],remaining_ambiguities=revised.unresolved,invented_geometry_added=False)
    return record_spatial_organization_state(workspace,revised,gain)

def test_791_import_790_survives_save_reload_and_stays_open():
    workspace=_workspace_789()
    request=json.loads((ROOT/"frontend"/"interview-discriminant-request-790.json").read_text())
    response=json.loads((ROOT/"frontend"/"interview-discriminant-response-790.json").read_text())
    workspace=import_spatial_interview_discriminant_response(workspace,request,response)
    loaded=MultiViewWorkspace.model_validate_json(workspace.model_dump_json())
    assert len(loaded.spatial_interview_discriminant_investigations)==1
    record=loaded.spatial_interview_discriminant_investigations[0]
    assert record.request_id=="interview-discriminant-790"
    assert record.source_uncertainty_id=="interview-790:p4-p5-wall-sector-correspondence"
    assert record.outcome=="AMBIGUOUS" and record.uncertainty_state=="OPEN" and record.resolved is False
    results={x.property_token:x for x in record.property_results}
    assert results["OPENING_TO_ROOF_EDGE_RELATION"].outcome=="CORRESPONDENCE_COMPATIBLE"
    assert results["OPENING_TO_ROOF_EDGE_RELATION"].relation_tokens==["BELOW"]
    assert results["OPENING_LAYOUT_ORDER"].outcome=="AMBIGUOUS"
    assert results["DISTINCTIVE_OPENING_CONFIGURATION"].outcome=="NOT_OBSERVABLE"
    assert results["NEIGHBOR_BOUNDARY_ORDER"].outcome=="AMBIGUOUS"
    assert {p.photo_index for p in record.provenance}=={4,5}
    assert all(p.pixel_cues for p in record.provenance)
    assert spatial_interview_discriminant_already_executed(loaded,request)
    with pytest.raises(ValueError,match="already executed"):
        import_spatial_interview_discriminant_response(loaded,request,response)
    assert all(i.status.value not in {"same_physical_object","likely_same"} for i in [*loaded.pass_1.identities,*loaded.pass_2.identities])

def test_791_response_790_validation_fails_closed():
    workspace=_workspace_789()
    request=json.loads((ROOT/"frontend"/"interview-discriminant-request-790.json").read_text())
    response=json.loads((ROOT/"frontend"/"interview-discriminant-response-790.json").read_text())
    bad=json.loads(json.dumps(response)); bad["provenance"][2]["roi"]=[0,0,1,1]
    with pytest.raises(ValueError,match="authorized observation ROI"):
        import_spatial_interview_discriminant_response(workspace,request,bad)
    bad=json.loads(json.dumps(response)); bad["property_results"][1]["relation_tokens"]=["SAME_PHYSICAL_OBJECT"]
    with pytest.raises(ValueError,match="relation token"):
        import_spatial_interview_discriminant_response(workspace,request,bad)
