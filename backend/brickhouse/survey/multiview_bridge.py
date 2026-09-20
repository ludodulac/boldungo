"""Conservative MultiViewWorkspace -> ArchitecturalSurvey bridge."""
from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field

from brickhouse.building import Facade, SourceInfo, SourceKind
from brickhouse.vision.multiview import CertaintyLevel, ClaimStatus, IdentityStatus, MultiViewWorkspace, VisibilityStatus
from .models import ArchitecturalSurvey, Certainty, ObservationKind, PhotoEvidence, PhotoView, RelationKind, SurveyObservation, SurveyRelation
from .reasoning import QuestionImpact, SurveyHypothesis, SurveyOpenQuestion, SurveyReasoningState


class BridgeDebtCode(str, Enum):
    UNKNOWN_CATEGORY = "unknown_category"
    UNRESOLVED_CONTRADICTION = "unresolved_contradiction"
    UNREPRESENTABLE_RELATION = "unrepresentable_relation"
    VISIBILITY_ASSESSMENT_ONLY = "visibility_assessment_only"
    ABSENCE_CLAIM = "absence_claim"


class BridgeDiagnostic(BaseModel):
    code: BridgeDebtCode
    statement: str
    source_refs: list[str] = Field(default_factory=list)
    photo_indexes: list[int] = Field(default_factory=list)


class MultiViewSurveyBridgeResult(BaseModel):
    survey_state: SurveyReasoningState
    diagnostics: list[BridgeDiagnostic] = Field(default_factory=list)


_KIND_MAP = {
    "building_boundary": ObservationKind.BUILDING_BOUNDARY, "terrain": ObservationKind.TERRAIN,
    "material": ObservationKind.MATERIAL, "weathering": ObservationKind.WEATHERING,
    "opening": ObservationKind.OPENING, "window": ObservationKind.OPENING,
    "door": ObservationKind.OPENING, "garage_door": ObservationKind.OPENING,
    "roof": ObservationKind.ROOF, "chimney": ObservationKind.CHIMNEY,
    "equipment": ObservationKind.EQUIPMENT, "volume": ObservationKind.VOLUME,
    "platform": ObservationKind.PLATFORM, "terrace": ObservationKind.PLATFORM,
    "landing": ObservationKind.PLATFORM, "stair": ObservationKind.STAIR,
    "occlusion": ObservationKind.OCCLUSION, "context": ObservationKind.CONTEXT,
}
_RELATION_MAP = {
    "connects_to": RelationKind.CONNECTS_TO, "adjacent_to": RelationKind.ADJACENT_TO,
    "aligned_with": RelationKind.ALIGNED_WITH, "supports": RelationKind.SUPPORTS,
    "part_of": RelationKind.PART_OF, "same_physical_object": RelationKind.SAME_PHYSICAL_OBJECT,
}
_RANK = {CertaintyLevel.UNKNOWN: 0, CertaintyLevel.UNPROVEN: 1, CertaintyLevel.PLAUSIBLE: 2, CertaintyLevel.CERTAIN: 3}


def _certainty(value):
    return {CertaintyLevel.CERTAIN: Certainty.CERTAIN, CertaintyLevel.PLAUSIBLE: Certainty.PLAUSIBLE,
            CertaintyLevel.UNPROVEN: Certainty.UNPROVEN, CertaintyLevel.UNKNOWN: Certainty.UNPROVEN}[value]


def _final_observations(workspace):
    result = {item.id: item for item in workspace.pass_1.observations}
    result.update({item.id: item for item in workspace.pass_2.observations})
    return result


def _identity_groups(workspace, eligible):
    groups = []
    for identity in workspace.pass_2.identities:
        if identity.status is not IdentityStatus.SAME_PHYSICAL_OBJECT or identity.certainty is not CertaintyLevel.CERTAIN:
            continue
        current = set(identity.observation_ids)
        if not current.issubset(set(eligible)):
            continue
        mapped_kinds = {_KIND_MAP[(eligible[x].proposed_category or "").lower()] for x in current}
        if len(mapped_kinds) != 1:
            continue
        overlaps = [group for group in groups if group & current]
        for group in overlaps:
            current |= group
            groups.remove(group)
        groups.append(current)
    grouped = set().union(*groups) if groups else set()
    groups.extend([{identifier} for identifier in eligible if identifier not in grouped])
    return groups


def workspace_to_survey(workspace: MultiViewWorkspace, *, survey_id: str, survey_name: str,
                        front_facade_photo_index: int | None = None) -> MultiViewSurveyBridgeResult:
    """Transfer only claims that Survey can represent without increasing certainty.

    A canonical front is optional at this pre-Survey boundary.  When capture
    metadata or a user confirmation establishes one, callers may supply its
    photo index; otherwise every source view remains orientation-neutral.
    """
    if front_facade_photo_index is not None and not 1 <= front_facade_photo_index <= workspace.photo_count:
        raise ValueError("front_facade_photo_index is outside workspace photos")
    local = _final_observations(workspace)
    diagnostics = []
    eligible = {}
    for identifier, item in local.items():
        if item.visibility in {VisibilityStatus.NON_VISIBLE, VisibilityStatus.OCCLUDED}:
            diagnostics.append(BridgeDiagnostic(code=BridgeDebtCode.VISIBILITY_ASSESSMENT_ONLY,
                statement="Non-visible/occluded evidence is not converted into absence or a positive Survey object.",
                source_refs=[identifier], photo_indexes=[item.photo_index]))
            continue
        if item.visibility is VisibilityStatus.ABSENT:
            diagnostics.append(BridgeDiagnostic(code=BridgeDebtCode.ABSENCE_CLAIM,
                statement="Survey v0.1 has no generic negative-observation contract; absence remains a bridge diagnostic.",
                source_refs=[identifier], photo_indexes=[item.photo_index]))
            continue
        if item.status is not ClaimStatus.OBSERVED or item.certainty.existence not in {CertaintyLevel.CERTAIN, CertaintyLevel.PLAUSIBLE}:
            continue
        if (item.proposed_category or "").lower() not in _KIND_MAP:
            diagnostics.append(BridgeDiagnostic(code=BridgeDebtCode.UNKNOWN_CATEGORY,
                statement="Observed category has no lossless Survey kind mapping.", source_refs=[identifier],
                photo_indexes=[item.photo_index]))
            continue
        eligible[identifier] = item

    observations = []
    local_to_survey = {}
    for group in _identity_groups(workspace, eligible):
        items = [eligible[x] for x in sorted(group)]
        kinds = {_KIND_MAP[(x.proposed_category or "").lower()] for x in items}
        if len(kinds) != 1:
            raise AssertionError("identity grouping must not merge incompatible Survey kinds")
        kind = next(iter(kinds))
        oid = "mv-" + "-".join(sorted(group))
        existence = min((x.certainty.existence for x in items), key=lambda x: _RANK[x])
        attrs, attr_certainty = {}, {}
        types = {(x.proposed_category or "").lower() for x in items}
        if kind is ObservationKind.OPENING and len(types) == 1 and next(iter(types)) in {"window", "door", "garage_door"}:
            semantic_type = next(iter(types))
            type_certainty = min((x.certainty.category for x in items), key=lambda x: _RANK[x])
            if type_certainty is not CertaintyLevel.UNKNOWN:
                attrs["semantic_type"] = semantic_type
                attr_certainty["semantic_type"] = _certainty(type_certainty)
        observations.append(SurveyObservation(id=oid, kind=kind, certainty=_certainty(existence),
            statement=" / ".join(dict.fromkeys(x.statement for x in items)),
            evidence=[PhotoEvidence(photo_index=x.photo_index, observation=x.statement, region=x.region) for x in items],
            attributes=attrs, attribute_certainty=attr_certainty))
        for identifier in group:
            local_to_survey[identifier] = oid

    relations = []
    for rel in workspace.pass_2.relations:
        subject, obj = local_to_survey.get(rel.subject_ref), local_to_survey.get(rel.object_ref)
        kind = _RELATION_MAP.get(rel.relation)
        if not subject or not obj or subject == obj or kind is None or not rel.supporting_photo_indexes:
            diagnostics.append(BridgeDiagnostic(code=BridgeDebtCode.UNREPRESENTABLE_RELATION,
                statement="Relation cannot be transferred losslessly to Survey.",
                source_refs=[rel.subject_ref, rel.object_ref], photo_indexes=rel.supporting_photo_indexes))
            continue
        if rel.status is ClaimStatus.UNKNOWN or rel.certainty is CertaintyLevel.UNKNOWN:
            continue
        relations.append(SurveyRelation(id="mv-"+rel.id, kind=kind, subject_id=subject, object_id=obj,
            certainty=_certainty(rel.certainty), statement="Workspace relation candidate: "+rel.relation,
            evidence=[PhotoEvidence(photo_index=i, observation="Workspace relation evidence: "+rel.relation)
                      for i in rel.supporting_photo_indexes]))

    questions = []
    for hyp in workspace.pass_2.hypotheses:
        subjects = sorted({local_to_survey[x] for x in hyp.subject_refs if x in local_to_survey})
        if subjects:
            questions.append(SurveyOpenQuestion(id="mv-hypothesis-"+hyp.id,
                question="Resolve hypothesis: "+hyp.statement, subject_observation_ids=subjects,
                hypotheses=[SurveyHypothesis(statement=hyp.statement, certainty=_certainty(hyp.certainty),
                    evidence=[PhotoEvidence(photo_index=i, observation=hyp.statement) for i in hyp.supporting_photo_indexes])],
                impact=QuestionImpact.MEDIUM, resolution_kind="cross_view_fusion"))
    for contradiction in workspace.pass_2.contradictions:
        if contradiction.resolved:
            continue
        diagnostics.append(BridgeDiagnostic(code=BridgeDebtCode.UNRESOLVED_CONTRADICTION,
            statement=contradiction.statement, source_refs=contradiction.claim_refs,
            photo_indexes=contradiction.photo_indexes))
        subjects = sorted({local_to_survey[x] for x in contradiction.claim_refs if x in local_to_survey})
        if subjects:
            questions.append(SurveyOpenQuestion(id="mv-contradiction-"+contradiction.id,
                question="Resolve contradiction: "+contradiction.statement, subject_observation_ids=subjects,
                impact=QuestionImpact.HIGH, resolution_kind="cross_view_fusion"))

    photos = [PhotoView(photo_index=i, capture_role="targeted_detail", facade=None,
        description="Source photo from pre-Survey multiview workspace.",
        source=SourceInfo(kind=SourceKind.OBSERVED, confidence=1.0), image_left_maps_to_facade_offset=None)
        for i in range(1, workspace.photo_count+1)]
    if front_facade_photo_index is not None:
        photos[front_facade_photo_index-1] = PhotoView(photo_index=front_facade_photo_index,
            capture_role="facade_view", facade=Facade.FRONT, description="Externally established canonical front view.",
            source=SourceInfo(kind=SourceKind.OBSERVED, confidence=1.0), image_left_maps_to_facade_offset="low")
    survey = ArchitecturalSurvey(id=survey_id, name=survey_name, photos=photos, known_measurements=[],
        observations=observations, relations=relations,
        notes="Generated conservatively from MultiViewWorkspace; no metric values synthesized.")
    return MultiViewSurveyBridgeResult(survey_state=SurveyReasoningState(survey=survey, open_questions=questions),
                                       diagnostics=diagnostics)
