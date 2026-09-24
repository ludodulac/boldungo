import json
from pathlib import Path
import pytest

from brickhouse.vision.multiview import (
    AssertionRevision, MultiViewWorkspace, RichEvidenceProvenance, RichVisualBootstrapResponse,
    SpatialOrganizationAssertion, SpatialOrganizationCandidate, ViewExplanationGain,
    build_rich_multiview_bootstrap_request, import_rich_visual_bootstrap_response,
    import_p3_perception_expansion_response, import_p5_perception_expansion_response, import_spatial_interview_discriminant_response, import_spatial_pixel_check_response,
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


def test_793_import_792_survives_save_reload_as_local_compatibility_not_identity():
    workspace=_workspace_789()
    request790=json.loads((ROOT/"frontend"/"interview-discriminant-request-790.json").read_text())
    response790=json.loads((ROOT/"frontend"/"interview-discriminant-response-790.json").read_text())
    workspace=import_spatial_interview_discriminant_response(workspace,request790,response790)
    request792=json.loads((ROOT/"frontend"/"interview-discriminant-request-792.json").read_text())
    response792=json.loads((ROOT/"frontend"/"interview-discriminant-response-792.json").read_text())
    workspace=import_spatial_interview_discriminant_response(workspace,request792,response792)
    loaded=MultiViewWorkspace.model_validate_json(workspace.model_dump_json())
    records={x.request_id:x for x in loaded.spatial_interview_discriminant_investigations}
    assert set(records)=={"interview-discriminant-790","interview-discriminant-792"}
    record=records["interview-discriminant-792"]
    assert record.source_uncertainty_id=="interview-792:p3-p5-lower-volume-opening-correspondence"
    assert record.outcome=="CORRESPONDENCE_COMPATIBLE"
    assert record.uncertainty_state=="LOCAL_COMPATIBILITY_ESTABLISHED"
    assert record.resolved is False
    results={x.property_token:x for x in record.property_results}
    assert results["LOWER_OPENING_CONTAINMENT"].relation_tokens==["CONTAINED_WITHIN"]
    assert results["OPENING_TO_LOWER_VOLUME_TOP_BOUNDARY_ORDER"].relation_tokens==["BELOW"]
    assert results["LOWER_VOLUME_OPENING_BOUNDARY_CONFIGURATION"].relation_tokens==["CONTAINED_WITHIN","BELOW"]
    assert {p.photo_index for p in record.provenance}=={3,5}
    assert all(p.pixel_cues for p in record.provenance)
    assert spatial_interview_discriminant_already_executed(loaded,request792)
    with pytest.raises(ValueError,match="already executed"):
        import_spatial_interview_discriminant_response(loaded,request792,response792)
    identities=[*loaded.pass_1.identities,*loaded.pass_2.identities]
    assert not any(set(i.observation_ids)=={"obs_p3_box_volume","obs_p5_side_wall"} for i in identities)
    assert not any(i.status.value in {"same_physical_object","likely_same"} and "obs_p3_box_volume" in i.observation_ids for i in identities)


def test_793_response_792_validation_fails_closed_without_promoting_p5_observation():
    workspace=_workspace_789()
    request=json.loads((ROOT/"frontend"/"interview-discriminant-request-792.json").read_text())
    response=json.loads((ROOT/"frontend"/"interview-discriminant-response-792.json").read_text())
    before={x.id for x in [*workspace.pass_1.observations,*workspace.pass_2.observations]}
    imported=import_spatial_interview_discriminant_response(workspace,request,response)
    after={x.id for x in [*imported.pass_1.observations,*imported.pass_2.observations]}
    assert after==before
    assert "obs_p5_side_wall" in after
    assert not any("lower" in x and x.startswith("obs_p5") for x in after if x!="obs_p5_side_wall")
    bad=json.loads(json.dumps(response)); bad["provenance"][2]["photo_index"]=4
    with pytest.raises(ValueError,match="outside authorized request"):
        import_spatial_interview_discriminant_response(workspace,request,bad)
    bad=json.loads(json.dumps(response)); bad["property_results"][0]["relation_tokens"]=["SAME_PHYSICAL_OBJECT"]
    with pytest.raises(ValueError,match="relation token"):
        import_spatial_interview_discriminant_response(workspace,request,bad)


def test_795_import_794_promotes_supported_regions_withholds_uncertain_wall_and_survives_reload():
    workspace=_workspace_789()
    request=json.loads((ROOT/"frontend"/"p3-perception-expansion-request-794.json").read_text())
    response=json.loads((ROOT/"frontend"/"p3-perception-expansion-response-794.json").read_text())
    before_identity=[*workspace.pass_1.identities,*workspace.pass_2.identities]
    workspace=import_p3_perception_expansion_response(workspace,request,response)
    loaded=MultiViewWorkspace.model_validate_json(workspace.model_dump_json())
    obs={x.id:x for x in [*loaded.pass_1.observations,*loaded.pass_2.observations]}
    assert set(["obs_p3_step_diagonal_794","obs_p3_raised_platform_794","obs_p3_visible_junction_794"])<=set(obs)
    assert [obs["obs_p3_step_diagonal_794"].region.x0,obs["obs_p3_step_diagonal_794"].region.y0,obs["obs_p3_step_diagonal_794"].region.x1,obs["obs_p3_step_diagonal_794"].region.y1]==[0.104,0.442,0.329,0.839]
    assert [obs["obs_p3_raised_platform_794"].region.x0,obs["obs_p3_raised_platform_794"].region.y0,obs["obs_p3_raised_platform_794"].region.x1,obs["obs_p3_raised_platform_794"].region.y1]==[0.345,0.459,0.688,0.675]
    assert [obs["obs_p3_visible_junction_794"].region.x0,obs["obs_p3_visible_junction_794"].region.y0,obs["obs_p3_visible_junction_794"].region.x1,obs["obs_p3_visible_junction_794"].region.y1]==[0.298,0.426,0.369,0.607]
    assert not any(x.id=="obs_p3_adjacent_wall_794" for x in obs.values())
    rec=loaded.p3_perception_expansion_investigations[-1]
    assert rec.request_id=="p3-perception-expansion-794" and rec.photo_index==3
    by={x.candidate_id:x for x in rec.candidates}
    assert by["p3-candidate-adjacent-wall-region"].disposition=="WITHHELD"
    assert by["p3-candidate-adjacent-wall-region"].epistemic_confidence=="PARTIALLY_BOUNDED"
    assert by["p3-candidate-adjacent-wall-region"].semantic_status=="UNCERTAIN"
    assert by["p3-candidate-adjacent-wall-region"].localized_roi==(0.105,0.176,0.354,0.686)
    assert all(x.visible_boundaries and x.pixel_cues for x in rec.candidates)
    assert rec.physical_identity_acquired is False and rec.invented_geometry_added is False
    assert [*loaded.pass_1.identities,*loaded.pass_2.identities]==before_identity
    keys=set(rec.imported_relation_keys)
    assert "obs_p3_step_diagonal_794|LEFT_OF|obs_p3_box_volume" in keys
    assert "obs_p3_raised_platform_794|ABOVE|obs_p3_dark_opening" in keys
    assert "obs_p3_raised_platform_794|BOUNDARY_JOINS|obs_p3_box_volume" in keys
    assert "obs_p3_step_diagonal_794|TERMINATES_AGAINST|obs_p3_visible_junction_794" in keys
    assert "obs_p3_visible_junction_794|LEFT_OF|obs_p3_raised_platform_794" in keys
    assert not any("adjacent_wall" in x for x in keys)
    assert all(r.provenance and all(p.photo_index==3 and p.pixel_cues for p in r.provenance)
               for r in loaded.rich_relation_evidence if any(y in {r.subject_ref,r.object_ref} for y in {"obs_p3_step_diagonal_794","obs_p3_raised_platform_794","obs_p3_visible_junction_794"}))


def test_795_promotions_remain_revisable_and_validation_fails_closed():
    workspace=_workspace_789()
    request=json.loads((ROOT/"frontend"/"p3-perception-expansion-request-794.json").read_text())
    response=json.loads((ROOT/"frontend"/"p3-perception-expansion-response-794.json").read_text())
    workspace=import_p3_perception_expansion_response(workspace,request,response)
    o=next(x for x in workspace.pass_2.observations if x.id=="obs_p3_step_diagonal_794")
    revised=record_assertion_revision(workspace,AssertionRevision(
        revision_id="test-795-revision",assertion_ref=o.id,previous_status=o.status.value,
        new_epistemic_state="REJECTED_BY_PIXELS",reason="test future correction",
        provenance=[RichEvidenceProvenance(observation_ref=o.id,photo_index=3,
            roi=(o.region.x0,o.region.y0,o.region.x1,o.region.y1),pixel_cues=["future contradictory pixel evidence"])]))
    assert revised.assertion_revisions[-1].assertion_ref=="obs_p3_step_diagonal_794"
    bad=json.loads(json.dumps(response)); bad["photo_index"]=5
    with pytest.raises(ValueError,match="request/photo mismatch"):
        import_p3_perception_expansion_response(_workspace_789(),request,bad)
    bad=json.loads(json.dumps(response)); bad["region_results"][0]["relations"][0]["relation_token"]="SAME_PHYSICAL_OBJECT"
    with pytest.raises(ValueError):
        import_p3_perception_expansion_response(_workspace_789(),request,bad)


def test_797_import_796_preserves_global_not_observable_and_property_level_constraints_after_reload():
    workspace=_workspace_789()
    req794=json.loads((ROOT/"frontend"/"p3-perception-expansion-request-794.json").read_text())
    res794=json.loads((ROOT/"frontend"/"p3-perception-expansion-response-794.json").read_text())
    workspace=import_p3_perception_expansion_response(workspace,req794,res794)
    before_obs={x.id for x in [*workspace.pass_1.observations,*workspace.pass_2.observations]}
    before_ids=[*workspace.pass_1.identities,*workspace.pass_2.identities]
    request=json.loads((ROOT/"frontend"/"composite-interview-discriminant-request-796.json").read_text())
    response=json.loads((ROOT/"frontend"/"composite-interview-discriminant-response-796.json").read_text())
    workspace=import_spatial_interview_discriminant_response(workspace,request,response)
    loaded=MultiViewWorkspace.model_validate_json(workspace.model_dump_json())
    record=next(x for x in loaded.spatial_interview_discriminant_investigations if x.request_id=="composite-interview-discriminant-796")
    assert record.outcome=="NOT_OBSERVABLE"
    assert record.uncertainty_state=="PARTIALLY_CONSTRAINED_NOT_FULLY_OBSERVABLE"
    assert record.resolved is False
    results={x.property_token:x for x in record.property_results}
    assert results["STEP_TO_PLATFORM_LATERAL_ORDER"].outcome=="CORRESPONDENCE_COMPATIBLE"
    assert results["STEP_TO_PLATFORM_LATERAL_ORDER"].relation_tokens==["LEFT_OF"]
    assert results["STEP_PLATFORM_TERMINATION_JUNCTION_CONFIGURATION"].outcome=="NOT_OBSERVABLE"
    assert results["STEP_PLATFORM_TERMINATION_JUNCTION_CONFIGURATION"].relation_tokens==["NO_RELIABLE_RELATION"]
    assert results["STEP_TO_PLATFORM_VERTICAL_ORDER"].outcome=="CORRESPONDENCE_COMPATIBLE"
    assert results["STEP_TO_PLATFORM_VERTICAL_ORDER"].relation_tokens==["BELOW"]
    assert {p.photo_index for p in record.provenance}=={3,4}
    assert all(p.pixel_cues for p in record.provenance)
    assert any(p.roi==(0.104,0.442,0.329,0.839) for p in record.provenance)
    assert any(p.roi==(0.19,0.29,0.38,0.56) for p in record.provenance)
    assert spatial_interview_discriminant_already_executed(loaded,request)
    with pytest.raises(ValueError,match="already executed"):
        import_spatial_interview_discriminant_response(loaded,request,response)
    assert {x.id for x in [*loaded.pass_1.observations,*loaded.pass_2.observations]}==before_obs
    assert [*loaded.pass_1.identities,*loaded.pass_2.identities]==before_ids


def test_797_response_796_validation_fails_closed_on_roi_identity_and_property_coverage():
    workspace=_workspace_789()
    request=json.loads((ROOT/"frontend"/"composite-interview-discriminant-request-796.json").read_text())
    response=json.loads((ROOT/"frontend"/"composite-interview-discriminant-response-796.json").read_text())
    bad=json.loads(json.dumps(response)); bad["provenance"][0]["roi"]=[0,0,1,1]
    with pytest.raises(ValueError,match="authorized observation ROI"):
        import_spatial_interview_discriminant_response(workspace,request,bad)
    bad=json.loads(json.dumps(response)); bad["property_results"][0]["relation_tokens"]=["SAME_PHYSICAL_OBJECT"]
    with pytest.raises(ValueError,match="relation token"):
        import_spatial_interview_discriminant_response(workspace,request,bad)
    bad=json.loads(json.dumps(response)); bad["property_results"]=bad["property_results"][:2]
    with pytest.raises(ValueError,match="exactly cover"):
        import_spatial_interview_discriminant_response(workspace,request,bad)


def test_798_existing_constraints_inform_but_do_not_bridge_without_shared_persistent_node():
    workspace=_workspace_789()
    req794=json.loads((ROOT/"frontend"/"p3-perception-expansion-request-794.json").read_text())
    res794=json.loads((ROOT/"frontend"/"p3-perception-expansion-response-794.json").read_text())
    workspace=import_p3_perception_expansion_response(workspace,req794,res794)
    req792=json.loads((ROOT/"frontend"/"interview-discriminant-request-792.json").read_text())
    res792=json.loads((ROOT/"frontend"/"interview-discriminant-response-792.json").read_text())
    workspace=import_spatial_interview_discriminant_response(workspace,req792,res792)
    req796=json.loads((ROOT/"frontend"/"composite-interview-discriminant-request-796.json").read_text())
    res796=json.loads((ROOT/"frontend"/"composite-interview-discriminant-response-796.json").read_text())
    workspace=import_spatial_interview_discriminant_response(workspace,req796,res796)
    before=workspace.model_dump()
    p5=next(x for x in workspace.spatial_view_predictions if x.prediction_id=="788-p5-sector-structure")
    assert p5.observation_refs==["obs_p5_side_wall"]
    assert p5.verification_relation_tokens==["LEFT_OF","BELOW","BOUNDARY_JOINS"]
    assert all(x.observation_ref=="obs_p5_side_wall" and x.photo_index==5 and x.roi==(0.13,0.04,0.88,0.79)
               for x in p5.verification_provenance)
    observations={x.id for x in [*workspace.pass_1.observations,*workspace.pass_2.observations]}
    assert "obs_p5_side_wall" in observations
    assert not any(x in observations for x in {"p5_stair_diagonal_sector","p5_platform_sector","obs_p5_stair","obs_p5_platform"})
    # Semantic stair/platform labels in P3/P4/P5 do not create a shared persistent node.
    p3={"obs_p3_step_diagonal_794","obs_p3_raised_platform_794"}
    p4={"obs_p4_stair","obs_p4_terrace"}
    assert p3<=observations and p4<=observations and p3.isdisjoint(p4)
    # 792 establishes local correspondence only; it explicitly does not establish physical identity.
    r792=next(x for x in workspace.spatial_interview_discriminant_investigations if x.request_id=="interview-discriminant-792")
    assert r792.uncertainty_state=="LOCAL_COMPATIBILITY_ESTABLISHED" and r792.resolved is False
    r796=next(x for x in workspace.spatial_interview_discriminant_investigations if x.request_id=="composite-interview-discriminant-796")
    assert r796.uncertainty_state=="PARTIALLY_CONSTRAINED_NOT_FULLY_OBSERVABLE" and r796.resolved is False
    # Read-only 798: no relation, observation, identity, or provenance is invented.
    assert workspace.model_dump()==before
    assert not any(i.status.value in {"same_physical_object","likely_same"} for i in [*workspace.pass_1.identities,*workspace.pass_2.identities])


def test_798_diagnostic_artifact_is_fail_closed_and_does_not_promote_p5_substructures():
    d=json.loads((ROOT/"frontend"/"existing-constraint-bridge-798.json").read_text())
    assert d["issue_798"]=="EXISTING_CONSTRAINTS_INFORM_BUT_DO_NOT_BRIDGE"
    assert d["new_constraint_persisted"] is False
    assert d["new_request_created"] is False
    assert d["identity_acquired"] is False and d["invented_geometry_added"] is False
    p5=d["p5_relations"]
    assert {x["relation"] for x in p5}=={"LEFT_OF","BELOW","BOUNDARY_JOINS"}
    assert all(x["source_observation_ref"]=="obs_p5_side_wall" for x in p5)
    assert all(x["roi"]==[0.13,0.04,0.88,0.79] for x in p5)
    assert all(x["subject_ref"]=="p5_stair_diagonal_sector" and x["object_ref"]=="p5_platform_sector" for x in p5)
    assert d["p5_substructures_are_local_observations"] is False
    assert d["composition_guard"]=="NO_COMPOSITION_WITHOUT_SHARED_PERSISTENT_NODE_OR_SUFFICIENT_ACQUIRED_CORRESPONDENCE"


def test_799_p5_perception_expansion_request_is_bounded_fail_closed_and_non_ingesting():
    d=json.loads((ROOT/"frontend"/"p5-perception-expansion-request-799.json").read_text())
    assert d["request_id"]=="p5-perception-expansion-799"
    assert d["authorized_photo"]["photo_index"]==5
    assert d["search_sector"]=={"observation_ref":"obs_p5_side_wall","photo_index":5,"search_roi":[0.13,0.04,0.88,0.79],"status":"PERSISTENT_LOCAL_OBSERVATION"}
    assert [x["candidate_id"] for x in d["candidate_searches"]]==[
        "p5-candidate-stair-diagonal-region","p5-candidate-platform-region","p5-candidate-stair-platform-junction"]
    assert d["allowed_outcomes"]==["LOCALIZABLE","AMBIGUOUS","NOT_OBSERVABLE"]
    assert d["allowed_relation_tokens"]==["LEFT_OF","RIGHT_OF","ABOVE","BELOW","BOUNDARY_JOINS","TERMINATES_AGAINST","NO_RELIABLE_RELATION"]
    assert d["memory_788"]["status"]=="REVISABLE_SEARCH_MEMORY_NOT_LOCAL_OBSERVATIONS"
    assert d["memory_788"]["prior_qualitative_relations"]==[
        ["p5_stair_diagonal_sector","LEFT_OF","p5_platform_sector"],
        ["p5_stair_diagonal_sector","BELOW","p5_platform_sector"],
        ["p5_stair_diagonal_sector","BOUNDARY_JOINS","p5_platform_sector"]]
    assert "REQUIRES_A_AND_B_SUFFICIENTLY_LOCALIZABLE" in d["candidate_searches"][2]["dependency"]
    assert d["automatic_ingestion"] is False
    joined=json.dumps(d)
    assert "No LocalObservation creation" in joined
    assert "Semantic interpretation is separate from localization" in joined
    assert "matching candidate_id, non-empty pixel_cues" in joined
    assert "No physical identity" in joined
    assert "SAME_PHYSICAL_OBJECT" in joined and "LIKELY_SAME" in joined
    assert "metric geometry" in joined and "camera pose" in joined
    assert "P3/P4 comparison" in joined
    assert "response may contradict it" in joined


def test_799_request_does_not_promote_p5_substructures_or_mutate_workspace():
    d=json.loads((ROOT/"frontend"/"p5-perception-expansion-request-799.json").read_text())
    workspace=_workspace_789()
    before=workspace.model_dump()
    obs={x.id for x in [*workspace.pass_1.observations,*workspace.pass_2.observations]}
    assert "obs_p5_side_wall" in obs
    assert not any(x in obs for x in {"p5_stair_diagonal_sector","p5_platform_sector","obs_p5_stair","obs_p5_platform"})
    assert d["memory_788"]["candidate_substructures"]==["p5_stair_diagonal_sector","p5_platform_sector"]
    assert workspace.model_dump()==before


def test_800_ingests_799_promotes_only_diagonal_revises_788_and_survives_reload():
    workspace=_workspace_789()
    request=json.loads((ROOT/"frontend"/"p5-perception-expansion-request-799.json").read_text())
    response=json.loads((ROOT/"frontend"/"p5-perception-expansion-response-799.json").read_text())
    before_ids=[*workspace.pass_1.identities,*workspace.pass_2.identities]
    loaded=MultiViewWorkspace.model_validate_json(import_p5_perception_expansion_response(workspace,request,response).model_dump_json())
    obs={x.id:x for x in [*loaded.pass_1.observations,*loaded.pass_2.observations]}
    assert "obs_p5_stair_diagonal_799" in obs
    o=obs["obs_p5_stair_diagonal_799"]
    assert (o.region.x0,o.region.y0,o.region.x1,o.region.y1)==(0.27,0.54,0.67,0.79)
    assert o.proposed_category=="diagonal/stair-like structural region"
    assert o.certainty.existence.value=="certain" and o.certainty.category.value=="plausible"
    assert not any(x in obs for x in {"obs_p5_platform_799","obs_p5_stair_platform_junction_799"})
    rec=loaded.p5_perception_expansion_investigations[-1]
    by={x.candidate_id:x for x in rec.candidates}
    assert by["p5-candidate-stair-diagonal-region"].disposition=="PROMOTED_LOCAL_OBSERVATION"
    assert by["p5-candidate-stair-diagonal-region"].localization_basis=="DIRECTLY_LOCALIZED"
    assert by["p5-candidate-stair-diagonal-region"].semantic_status=="SUPPORTED_AS_INTERPRETATION"
    assert by["p5-candidate-stair-diagonal-region"].provenance.roi==(0.27,0.54,0.67,0.79)
    assert by["p5-candidate-platform-region"].outcome=="AMBIGUOUS" and by["p5-candidate-platform-region"].disposition=="WITHHELD"
    assert by["p5-candidate-platform-region"].candidate_roi is None and by["p5-candidate-platform-region"].semantic_status=="UNCERTAIN"
    assert by["p5-candidate-stair-platform-junction"].outcome=="NOT_OBSERVABLE" and by["p5-candidate-stair-platform-junction"].disposition=="WITHHELD"
    assert by["p5-candidate-stair-platform-junction"].candidate_roi is None
    assert all(x.provenance.photo_index==5 and x.provenance.pixel_cues for x in rec.candidates)
    pred=next(x for x in loaded.spatial_view_predictions if x.prediction_id=="788-p5-sector-structure")
    assert pred.verification_relation_tokens==["LEFT_OF","BELOW","BOUNDARY_JOINS"]  # historical trace retained
    assert pred.current_support_status=="HISTORICAL_CANDIDATE_MEMORY"
    rev=next(x for x in loaded.assertion_revisions if x.revision_id=="revision-800-p5-788-sector")
    assert rev.assertion_ref=="788-p5-sector-structure" and rev.new_epistemic_state=="SUPERSEDED"
    assert "platform remains AMBIGUOUS" in rev.reason and "junction NOT_OBSERVABLE" in rev.reason
    assert not any(r.relation_token=="BOUNDARY_JOINS" and "obs_p5_stair_diagonal_799" in {r.subject_ref,r.object_ref} for r in loaded.rich_relation_evidence)
    assert [*loaded.pass_1.identities,*loaded.pass_2.identities]==before_ids
    assert rec.physical_identity_acquired is False and rec.invented_geometry_added is False


def test_800_validation_fails_closed_and_799_cannot_create_platform_or_junction_relation():
    workspace=_workspace_789()
    request=json.loads((ROOT/"frontend"/"p5-perception-expansion-request-799.json").read_text())
    response=json.loads((ROOT/"frontend"/"p5-perception-expansion-response-799.json").read_text())
    bad=json.loads(json.dumps(response)); bad["photo_index"]=4
    with pytest.raises(ValueError,match="identity/photo"):
        import_p5_perception_expansion_response(workspace,request,bad)
    bad=json.loads(json.dumps(response)); bad["candidate_results"][1]["candidate_roi"]=[0.4,0.4,0.5,0.5]
    with pytest.raises(ValueError,match="must not have ROI"):
        import_p5_perception_expansion_response(workspace,request,bad)
    bad=json.loads(json.dumps(response)); bad["candidate_results"][2]["relations"]=["BOUNDARY_JOINS"]
    # Even an allowed token cannot override the required 799 epistemic result into a persisted relation.
    imported=import_p5_perception_expansion_response(workspace,request,bad)
    assert not any(r.relation_token=="BOUNDARY_JOINS" and "obs_p5_stair_diagonal_799" in {r.subject_ref,r.object_ref} for r in imported.rich_relation_evidence)


def test_801_request_is_new_p5_only_fail_closed_and_non_ingesting():
    request=json.loads((ROOT/"frontend"/"p5-platform-discriminant-request-801.json").read_text())
    prior=json.loads((ROOT/"frontend"/"p5-perception-expansion-request-799.json").read_text())
    assert request["schema_version"]=="0.1" and request["request_id"]=="p5-platform-discriminant-801"
    assert request["authorized_photo"]["photo_index"]==5
    refs={x["observation_ref"] for x in request["authorized_observations"]}
    assert refs=={"obs_p5_side_wall","obs_p5_stair_diagonal_799"}
    workspace=_workspace_789()
    workspace=import_p5_perception_expansion_response(workspace,prior,json.loads((ROOT/"frontend"/"p5-perception-expansion-response-799.json").read_text()))
    real={x.id for x in [*workspace.pass_1.observations,*workspace.pass_2.observations]}
    assert refs <= real
    assert request["new_information_sought"]["property_token"]=="HORIZONTAL_SURFACE_VERTICAL_FACE_BOUNDARY_SEPARATION"
    assert "LOCALIZABLE" not in request["allowed_outcomes"]
    assert {"SUPPORTED","CONTRADICTED","AMBIGUOUS","NOT_OBSERVABLE"}==set(request["allowed_outcomes"])
    assert request["automatic_ingestion"] is False
    serialized=json.dumps(request)
    assert "HISTORICAL_CANDIDATE_MEMORY" in serialized
    assert '"outcome": "AMBIGUOUS"' in serialized and '"outcome": "NOT_OBSERVABLE"' in serialized
    assert "DIRECTLY_LOCALIZED" in serialized
    assert "Do not repeat 799" in serialized
    assert "near-horizontal upper boundary alone is insufficient" in serialized
    assert "Do not restore 788 LEFT_OF, BELOW or BOUNDARY_JOINS" in serialized
    assert "No physical identity" in serialized
    assert "No LocalObservation creation" in serialized
    assert request["new_information_sought"]["property_token"] not in json.dumps(prior)


def test_801_request_does_not_promote_platform_or_restore_788_relations():
    request=json.loads((ROOT/"frontend"/"p5-platform-discriminant-request-801.json").read_text())
    refs={x["observation_ref"] for x in request["authorized_observations"]}
    assert "p5_platform_sector" not in refs and "obs_p5_platform_799" not in refs
    assert request["anti_repeat_memory"]["memory_788"]["status"]=="HISTORICAL_CANDIDATE_MEMORY"
    assert request["anti_repeat_memory"]["memory_788"]["historical_tokens"]==["LEFT_OF","BELOW","BOUNDARY_JOINS"]
    assert request["anti_repeat_memory"]["investigation_799"]["platform"]["candidate_roi"] is None
    assert request["anti_repeat_memory"]["investigation_799"]["junction"]["candidate_roi"] is None
    assert request["response_schema"]["properties"]["photo_index"]["const"]==5
    assert "NOT_OBSERVABLE" in request["response_schema"]["properties"]["outcome"]["enum"]
