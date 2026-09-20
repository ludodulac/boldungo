from brickhouse.vision.multiview import (
    ArchitecturalRelationCandidate, AspectCertainty, CertaintyLevel, ClaimStatus,
    Contradiction, IdentityCandidate, IdentityStatus, LocalObservation,
    MultiViewPass, MultiViewWorkspace, OpenHypothesis, ViewAssessment, VisibilityStatus,
)
from brickhouse.survey.models import Certainty, ObservationKind
from brickhouse.survey.multiview_bridge import BridgeDebtCode, workspace_to_survey


def obs(identifier, photo, category="opening", category_certainty=CertaintyLevel.CERTAIN):
    return LocalObservation(id=identifier, photo_index=photo, status=ClaimStatus.OBSERVED,
        visibility=VisibilityStatus.VISIBLE, proposed_category=category,
        statement=f"{category} visible", certainty=AspectCertainty(
            existence=CertaintyLevel.CERTAIN, category=category_certainty,
            metric=CertaintyLevel.UNKNOWN))


def workspace(observations, *, identities=None, relations=None, hypotheses=None,
              contradictions=None, assessments=None):
    return MultiViewWorkspace(photo_count=max([x.photo_index for x in observations] + [2]),
        pass_1=MultiViewPass(pass_number=1, observations=observations),
        pass_2=MultiViewPass(pass_number=2, observations=observations,
            identities=identities or [], relations=relations or [],
            hypotheses=hypotheses or [], contradictions=contradictions or [],
            view_assessments=assessments or []))


def bridge(ws):
    return workspace_to_survey(ws, survey_id="synthetic", survey_name="Synthetic", front_facade_photo_index=1)


def test_a_certain_same_window_fuses_with_multiview_provenance():
    a, b = obs("a", 1, "window"), obs("b", 2, "window")
    identity = IdentityCandidate(id="same", observation_ids=["a","b"],
        status=IdentityStatus.SAME_PHYSICAL_OBJECT, corroborating_photo_indexes=[1,2],
        certainty=CertaintyLevel.CERTAIN)
    result=bridge(workspace([a,b], identities=[identity]))
    assert len(result.survey_state.survey.observations)==1
    item=result.survey_state.survey.observations[0]
    assert {e.photo_index for e in item.evidence}=={1,2}
    assert "multiview_identity" not in item.attributes


def test_b_opening_existence_certain_but_door_type_stays_plausible():
    item=obs("a",1,"door",CertaintyLevel.PLAUSIBLE)
    result=bridge(workspace([item])).survey_state.survey.observations[0]
    assert result.certainty is Certainty.CERTAIN
    assert result.kind is ObservationKind.OPENING
    assert result.attributes["semantic_type"]=="door"
    assert result.attribute_certainty["semantic_type"] is Certainty.PLAUSIBLE


def test_c_occluded_other_view_never_creates_absence():
    a=obs("a",1,"window")
    hidden=LocalObservation(id="hidden", photo_index=2, status=ClaimStatus.UNKNOWN,
        visibility=VisibilityStatus.OCCLUDED, statement="region blocked")
    result=bridge(workspace([a,hidden]))
    assert len(result.survey_state.survey.observations)==1
    assert any(x.code is BridgeDebtCode.VISIBILITY_ASSESSMENT_ONLY for x in result.diagnostics)
    assert not any("absent" in x.statement.lower() for x in result.survey_state.survey.observations)


def test_d_incompatible_similar_objects_are_never_fused():
    a,b=obs("a",1,"window"),obs("b",2,"window")
    identity=IdentityCandidate(id="no",observation_ids=["a","b"],status=IdentityStatus.INCOMPATIBLE,
        conflicting_photo_indexes=[1,2],certainty=CertaintyLevel.CERTAIN)
    result=bridge(workspace([a,b],identities=[identity]))
    assert len(result.survey_state.survey.observations)==2


def test_e_competing_topology_hypotheses_do_not_create_topology_fact():
    stair=obs("stair",1,"stair")
    h1=OpenHypothesis(id="straight",subject_refs=["stair"],statement="stair may continue straight",
        competing_with=["turn"],supporting_photo_indexes=[1])
    h2=OpenHypothesis(id="turn",subject_refs=["stair"],statement="stair may turn",
        competing_with=["straight"],supporting_photo_indexes=[2])
    result=bridge(workspace([stair],hypotheses=[h1,h2]))
    survey_item=result.survey_state.survey.observations[0]
    assert "stair_topology" not in survey_item.attributes
    assert len(result.survey_state.open_questions)==2


def test_f_plausible_spatial_relation_stays_plausible():
    a,b=obs("a",1,"stair"),obs("b",2,"platform")
    rel=ArchitecturalRelationCandidate(id="join",subject_ref="a",object_ref="b",
        relation="connects_to",status=ClaimStatus.INFERRED,certainty=CertaintyLevel.PLAUSIBLE,
        supporting_photo_indexes=[1,2])
    result=bridge(workspace([a,b],relations=[rel]))
    assert result.survey_state.survey.relations[0].certainty is Certainty.PLAUSIBLE


def test_g_no_metric_evidence_creates_no_metric_values():
    result=bridge(workspace([obs("a",1,"window")])).survey_state.survey
    assert result.known_measurements==[]
    item=result.observations[0]
    forbidden={"width","height","depth","pitch_degrees","step_count","position"}
    assert forbidden.isdisjoint(item.attributes)


def test_h_unresolved_contradiction_survives_as_diagnostic_and_question():
    a,b=obs("a",1,"stair"),obs("b",2,"stair")
    contradiction=Contradiction(id="c",claim_refs=["a","b"],statement="topology conflicts",
        photo_indexes=[1,2],resolved=False)
    result=bridge(workspace([a,b],contradictions=[contradiction]))
    assert any(x.code is BridgeDebtCode.UNRESOLVED_CONTRADICTION for x in result.diagnostics)
    assert any("Resolve contradiction" in x.question for x in result.survey_state.open_questions)


def test_likely_same_is_not_promoted_to_same_physical_object():
    a,b=obs("a",1,"window"),obs("b",2,"window")
    identity=IdentityCandidate(id="maybe",observation_ids=["a","b"],status=IdentityStatus.LIKELY_SAME,
        corroborating_photo_indexes=[1,2],certainty=CertaintyLevel.PLAUSIBLE)
    result=bridge(workspace([a,b],identities=[identity]))
    assert len(result.survey_state.survey.observations)==2
    assert all("multiview_identity" not in x.attributes for x in result.survey_state.survey.observations)
