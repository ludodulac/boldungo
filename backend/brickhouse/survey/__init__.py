"""Architectural survey: photo observations before scene reconstruction."""

from .audit import (
    SurveyAudit,
    SurveyAuditFinding,
    SurveyAuditFindingStatus,
    SurveyAuditSeverity,
    SurveyAuditStatus,
    SurveyAuditSuggestedAction,
    SurveyAuditSummary,
    SurveyAuditTargetType,
    SurveyAuditValidationIssue,
    validate_survey_audit,
)
from .benchmark import (
    SurveyAuditBenchmarkCategory,
    SurveyAuditBenchmarkDecision,
    SurveyAuditBenchmarkLabel,
    SurveyAuditBenchmarkMetrics,
    SurveyAuditBenchmarkRun,
    SurveyAuditBenchmarkScorecard,
    SurveyAuditFindingAdjudication,
    SurveyAuditGoldAnomaly,
    compute_survey_audit_benchmark_metrics,
    evaluate_survey_audit_experimental_go,
)
from .correction import (
    SurveyCorrection,
    SurveyCorrectionChange,
    SurveyCorrectionObjectType,
    SurveyCorrectionValidationIssue,
    validate_survey_correction,
)
from .correction_eligibility import (
    SurveyCorrectionEligibility,
    automatic_survey_correction_finding_ids_v01,
    classify_survey_correction_finding_v01,
    survey_correction_eligibility_v01,
)
from .correction_reaudit import (
    SurveyCorrectionReauditScope,
    build_survey_correction_reaudit_scope,
)
from .correction_reaudit_contract import (
    SurveyCorrectionReaudit,
    SurveyCorrectionReauditValidationIssue,
    validate_survey_correction_reaudit,
)
from .human_facts import HumanAttributeFact, HumanFactApplication, apply_human_attribute_facts
from .human_spatial_facts import (
    HumanLevelRelation,
    HumanRelativeLevelFact,
    HumanRelativeLevelFactSet,
    validate_human_relative_level_facts,
)
from .models import (
    ArchitecturalSurvey,
    CanonicalFrame,
    Certainty,
    KnownMeasurement,
    KnowledgeMode,
    NormalizedImageRegion,
    ObservationKind,
    OpeningVisualDescription,
    PhotoEvidence,
    PhotoView,
    RelationKind,
    RepresentationPolicy,
    StructureRole,
    SurfaceAppearance,
    SurveyObservation,
    SurveyRelation,
)
from .multiview_identity import (
    MultiViewIdentityFacts,
    MultiViewIdentityReport,
    MultiViewIdentityValue,
    analyze_multiview_identity,
    validate_multiview_identity,
)
from .ownership import (
    OwnershipFacts,
    OwnershipReport,
    SubjectOwnership,
    analyze_subject_ownership,
    validate_subject_ownership,
)
from .reasoning import (
    QuestionImpact,
    SurveyHypothesis,
    SurveyOpenQuestion,
    SurveyReasoningState,
    rank_questions_for_user_input,
)
from .roof_guard import validate_multiview_roof_hypotheses
from .stair_topology import (
    StairTopologyFacts,
    StairTopologyReport,
    StairTopologyValue,
    analyze_survey_stair_topology,
    validate_stair_topology_observations,
)
from .validation import (
    SurveyValidationIssue,
    validate_survey_extension as _validate_survey_extension,
    validate_survey_semantics as _validate_survey_semantics,
)


def validate_survey_semantics(survey: ArchitecturalSurvey) -> list[SurveyValidationIssue]:
    """Run core Survey semantics plus targeted anti-loss guards."""
    return [
        *_validate_survey_semantics(survey),
        *validate_multiview_roof_hypotheses(survey),
        *validate_stair_topology_observations(survey),
        *validate_subject_ownership(survey),
        *validate_multiview_identity(survey),
    ]


def validate_survey_extension(
    base: ArchitecturalSurvey,
    candidate: ArchitecturalSurvey,
) -> list[SurveyValidationIssue]:
    """Run append-only extension validation plus targeted anti-loss guards."""
    issues = _validate_survey_extension(base, candidate)
    targeted_issues = [
        *validate_multiview_roof_hypotheses(candidate),
        *validate_stair_topology_observations(candidate),
        *validate_subject_ownership(candidate),
        *validate_multiview_identity(candidate),
    ]
    existing = {(issue.code, issue.observation_id) for issue in issues}
    issues.extend(
        issue
        for issue in targeted_issues
        if (issue.code, issue.observation_id) not in existing
    )
    return issues


__all__ = [
    "ArchitecturalSurvey",
    "CanonicalFrame",
    "Certainty",
    "HumanAttributeFact",
    "HumanFactApplication",
    "HumanLevelRelation",
    "HumanRelativeLevelFact",
    "HumanRelativeLevelFactSet",
    "KnownMeasurement",
    "KnowledgeMode",
    "MultiViewIdentityFacts",
    "MultiViewIdentityReport",
    "MultiViewIdentityValue",
    "NormalizedImageRegion",
    "ObservationKind",
    "OpeningVisualDescription",
    "OwnershipFacts",
    "OwnershipReport",
    "PhotoEvidence",
    "PhotoView",
    "QuestionImpact",
    "RelationKind",
    "RepresentationPolicy",
    "StairTopologyFacts",
    "StairTopologyReport",
    "StairTopologyValue",
    "SubjectOwnership",
    "StructureRole",
    "SurfaceAppearance",
    "SurveyAudit",
    "SurveyAuditBenchmarkCategory",
    "SurveyAuditBenchmarkDecision",
    "SurveyAuditBenchmarkLabel",
    "SurveyAuditBenchmarkMetrics",
    "SurveyAuditBenchmarkRun",
    "SurveyAuditBenchmarkScorecard",
    "SurveyAuditFinding",
    "SurveyAuditFindingAdjudication",
    "SurveyAuditFindingStatus",
    "SurveyAuditGoldAnomaly",
    "SurveyAuditSeverity",
    "SurveyAuditStatus",
    "SurveyAuditSuggestedAction",
    "SurveyAuditSummary",
    "SurveyAuditTargetType",
    "SurveyAuditValidationIssue",
    "SurveyCorrection",
    "SurveyCorrectionChange",
    "SurveyCorrectionEligibility",
    "SurveyCorrectionObjectType",
    "SurveyCorrectionReaudit",
    "SurveyCorrectionReauditScope",
    "SurveyCorrectionReauditValidationIssue",
    "SurveyCorrectionValidationIssue",
    "SurveyHypothesis",
    "SurveyObservation",
    "SurveyOpenQuestion",
    "SurveyReasoningState",
    "SurveyRelation",
    "SurveyValidationIssue",
    "analyze_multiview_identity",
    "analyze_subject_ownership",
    "analyze_survey_stair_topology",
    "apply_human_attribute_facts",
    "automatic_survey_correction_finding_ids_v01",
    "build_survey_correction_reaudit_scope",
    "classify_survey_correction_finding_v01",
    "compute_survey_audit_benchmark_metrics",
    "evaluate_survey_audit_experimental_go",
    "rank_questions_for_user_input",
    "survey_correction_eligibility_v01",
    "validate_human_relative_level_facts",
    "validate_multiview_identity",
    "validate_stair_topology_observations",
    "validate_subject_ownership",
    "validate_survey_audit",
    "validate_survey_correction",
    "validate_survey_correction_reaudit",
    "validate_survey_extension",
    "validate_survey_semantics",
    "validate_multiview_roof_hypotheses",
]
