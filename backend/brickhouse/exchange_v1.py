"""Validation core for the BOLDÜNGO boldungo.exchange.v1 contract."""

from __future__ import annotations

from datetime import datetime, timedelta
from enum import Enum
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StrictBool, TypeAdapter, field_validator, model_validator


SCHEMA_VERSION = "boldungo.exchange.v1"

ObservationId = Annotated[str, Field(pattern=r"^O\d{3,}$")]
HumanFactId = Annotated[str, Field(pattern=r"^HF\d{3,}$")]
EntityId = Annotated[str, Field(pattern=r"^E\d{3,}$")]
RelationId = Annotated[str, Field(pattern=r"^R\d{3,}$")]
UncertaintyId = Annotated[str, Field(pattern=r"^U\d{3,}$")]
QuestionId = Annotated[str, Field(pattern=r"^Q\d{3,}$")]
RoundId = Annotated[str, Field(pattern=r"^R\d{3,}$")]
PhotoId = Annotated[str, Field(pattern=r"^(FRONT|RIGHT|LEFT|REAR)_\d{3,}$")]


class _ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class MessageType(str, Enum):
    ANALYSIS_RESULT = "ANALYSIS_RESULT"
    HUMAN_ANSWERS = "HUMAN_ANSWERS"


class EntityType(str, Enum):
    VOLUME = "VOLUME"
    SURFACE = "SURFACE"
    OPENING = "OPENING"
    ASSEMBLY = "ASSEMBLY"
    SITE_ELEMENT = "SITE_ELEMENT"
    OTHER_PHYSICAL = "OTHER_PHYSICAL"


class RelationType(str, Enum):
    PART_OF = "PART_OF"
    CONNECTED_TO = "CONNECTED_TO"
    ABOVE = "ABOVE"
    LEFT_OF = "LEFT_OF"
    IN_FRONT_OF = "IN_FRONT_OF"
    ALIGNED_WITH = "ALIGNED_WITH"
    SAME_LEVEL_AS = "SAME_LEVEL_AS"
    CONTINUOUS_WITH = "CONTINUOUS_WITH"


class UncertaintyType(str, Enum):
    AMBIGUOUS = "AMBIGUOUS"
    PARTIALLY_OBSERVABLE = "PARTIALLY_OBSERVABLE"
    NOT_OBSERVABLE = "NOT_OBSERVABLE"


class ResolutionState(str, Enum):
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"


class QuestionScope(str, Enum):
    PHOTO = "PHOTO"
    GLOBAL = "GLOBAL"


class AnswerType(str, Enum):
    YES_NO = "YES_NO"
    SINGLE_CHOICE = "SINGLE_CHOICE"
    FREE_TEXT = "FREE_TEXT"


class AnswerState(str, Enum):
    ANSWERED = "ANSWERED"
    UNKNOWN = "UNKNOWN"


def _ensure_nonempty(value: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _ensure_unique(values: list[str], label: str) -> list[str]:
    if len(values) != len(set(values)):
        raise ValueError(f"{label} must not contain duplicate IDs")
    return values


def _validate_package_id(value: str) -> str:
    value = _ensure_nonempty(value, "package_id")
    if not value.startswith("PKG_"):
        raise ValueError("package_id must use PKG_<UUIDv4>")
    try:
        parsed = UUID(value[4:])
    except ValueError as exc:
        raise ValueError("package_id must use PKG_<UUIDv4>") from exc
    if parsed.version != 4 or value != f"PKG_{parsed}":
        raise ValueError("package_id must use canonical PKG_<UUIDv4>")
    return value


class Observation(_ContractModel):
    observation_id: ObservationId
    photo_id: PhotoId
    region_hint: str
    observation_text: str

    @field_validator("region_hint", "observation_text")
    @classmethod
    def nonempty_text(cls, value: str) -> str:
        return _ensure_nonempty(value, "observation text")


class HumanFact(_ContractModel):
    human_fact_id: HumanFactId
    source_round_id: RoundId
    source_question_id: QuestionId
    source_package_id: str
    fact_text: str

    @field_validator("source_package_id")
    @classmethod
    def package_id_format(cls, value: str) -> str:
        return _validate_package_id(value)

    @field_validator("fact_text")
    @classmethod
    def nonempty_fact(cls, value: str) -> str:
        return _ensure_nonempty(value, "fact_text")


class Entity(_ContractModel):
    entity_id: EntityId
    entity_type: EntityType
    description: str
    observation_refs: list[ObservationId] = Field(min_length=1)

    @field_validator("description")
    @classmethod
    def nonempty_description(cls, value: str) -> str:
        return _ensure_nonempty(value, "description")

    @field_validator("observation_refs")
    @classmethod
    def unique_observations(cls, value: list[str]) -> list[str]:
        return _ensure_unique(value, "entity.observation_refs")


class Relation(_ContractModel):
    relation_id: RelationId
    relation_type: RelationType
    subject_entity_id: EntityId
    object_entity_id: EntityId
    observation_refs: list[ObservationId] = Field(min_length=1)

    @field_validator("observation_refs")
    @classmethod
    def unique_observations(cls, value: list[str]) -> list[str]:
        return _ensure_unique(value, "relation.observation_refs")

    @model_validator(mode="after")
    def distinct_entities(self) -> "Relation":
        if self.subject_entity_id == self.object_entity_id:
            raise ValueError("relation subject_entity_id and object_entity_id must differ")
        return self


class Uncertainty(_ContractModel):
    uncertainty_id: UncertaintyId
    uncertainty_type: UncertaintyType
    description: str
    observation_refs: list[ObservationId]
    entity_refs: list[EntityId]
    relation_refs: list[RelationId]
    resolution_state: ResolutionState
    resolved_by_human_fact_refs: list[HumanFactId]
    resolved_by_observation_refs: list[ObservationId]

    @field_validator("description")
    @classmethod
    def nonempty_description(cls, value: str) -> str:
        return _ensure_nonempty(value, "description")

    @field_validator(
        "observation_refs",
        "entity_refs",
        "relation_refs",
        "resolved_by_human_fact_refs",
        "resolved_by_observation_refs",
    )
    @classmethod
    def unique_refs(cls, value: list[str], info) -> list[str]:
        return _ensure_unique(value, f"uncertainty.{info.field_name}")

    @model_validator(mode="after")
    def validate_uncertainty(self) -> "Uncertainty":
        if not (self.observation_refs or self.entity_refs or self.relation_refs):
            raise ValueError("uncertainty requires at least one observation/entity/relation reference")
        if self.resolution_state is ResolutionState.OPEN:
            if self.resolved_by_human_fact_refs or self.resolved_by_observation_refs:
                raise ValueError("OPEN uncertainty cannot contain resolution references")
        elif not (self.resolved_by_human_fact_refs or self.resolved_by_observation_refs):
            raise ValueError("RESOLVED uncertainty requires at least one resolution reference")
        overlap = set(self.observation_refs) & set(self.resolved_by_observation_refs)
        if overlap:
            raise ValueError("historical observation_refs and resolved_by_observation_refs must be disjoint")
        return self


class Choice(_ContractModel):
    value: str
    label: str

    @field_validator("value")
    @classmethod
    def technical_value(cls, value: str) -> str:
        value = _ensure_nonempty(value, "choice.value")
        if not value.isascii():
            raise ValueError("choice.value must be ASCII")
        return value

    @field_validator("label")
    @classmethod
    def nonempty_label(cls, value: str) -> str:
        return _ensure_nonempty(value, "choice.label")


class Question(_ContractModel):
    question_id: QuestionId
    scope: QuestionScope
    photo_refs: list[PhotoId]
    subject_hint: str | None
    question_text: str
    answer_type: AnswerType
    choices: list[Choice]
    allow_unknown: StrictBool
    uncertainty_refs: list[UncertaintyId] = Field(min_length=1)

    @field_validator("photo_refs", "uncertainty_refs")
    @classmethod
    def unique_refs(cls, value: list[str], info) -> list[str]:
        return _ensure_unique(value, f"question.{info.field_name}")

    @field_validator("question_text")
    @classmethod
    def nonempty_question(cls, value: str) -> str:
        return _ensure_nonempty(value, "question_text")

    @model_validator(mode="after")
    def validate_question_shape(self) -> "Question":
        if self.scope is QuestionScope.PHOTO:
            if not self.photo_refs:
                raise ValueError("PHOTO question requires at least one photo_ref")
            if self.subject_hint is None or not self.subject_hint.strip():
                raise ValueError("PHOTO question requires non-empty subject_hint")
        else:
            if self.photo_refs:
                raise ValueError("GLOBAL question requires photo_refs=[]")
            if self.subject_hint is not None:
                raise ValueError("GLOBAL question requires subject_hint=null")

        if self.answer_type is AnswerType.SINGLE_CHOICE:
            if len(self.choices) < 2:
                raise ValueError("SINGLE_CHOICE requires at least two choices")
            values = [choice.value for choice in self.choices]
            _ensure_unique(values, "question.choices.value")
        elif self.choices:
            raise ValueError("choices must be empty unless answer_type=SINGLE_CHOICE")
        return self


class Analysis(_ContractModel):
    observations: list[Observation]
    human_facts: list[HumanFact]
    entities: list[Entity]
    relations: list[Relation]
    uncertainties: list[Uncertainty]


class AnalysisResultPayload(_ContractModel):
    analysis: Analysis
    questions: list[Question]

    @model_validator(mode="after")
    def validate_internal_references(self) -> "AnalysisResultPayload":
        observations = {item.observation_id for item in self.analysis.observations}
        human_facts = {item.human_fact_id for item in self.analysis.human_facts}
        entities = {item.entity_id for item in self.analysis.entities}
        relations = {item.relation_id for item in self.analysis.relations}
        uncertainties = {item.uncertainty_id for item in self.analysis.uncertainties}

        def require_unique(items: list[Any], attr: str, label: str) -> None:
            values = [getattr(item, attr) for item in items]
            if len(values) != len(set(values)):
                raise ValueError(f"{label} IDs must be unique")

        require_unique(self.analysis.observations, "observation_id", "observation")
        require_unique(self.analysis.human_facts, "human_fact_id", "human_fact")
        require_unique(self.analysis.entities, "entity_id", "entity")
        require_unique(self.analysis.relations, "relation_id", "relation")
        require_unique(self.analysis.uncertainties, "uncertainty_id", "uncertainty")
        require_unique(self.questions, "question_id", "question")

        for entity in self.analysis.entities:
            unknown = set(entity.observation_refs) - observations
            if unknown:
                raise ValueError(f"entity {entity.entity_id} references unknown observations: {sorted(unknown)}")

        symmetric_seen: set[tuple[str, str, str]] = set()
        symmetric_types = {
            RelationType.CONNECTED_TO,
            RelationType.ALIGNED_WITH,
            RelationType.SAME_LEVEL_AS,
            RelationType.CONTINUOUS_WITH,
        }
        for relation in self.analysis.relations:
            if relation.subject_entity_id not in entities or relation.object_entity_id not in entities:
                raise ValueError(f"relation {relation.relation_id} references unknown entity")
            unknown = set(relation.observation_refs) - observations
            if unknown:
                raise ValueError(f"relation {relation.relation_id} references unknown observations: {sorted(unknown)}")
            if relation.relation_type in symmetric_types:
                pair = tuple(sorted((relation.subject_entity_id, relation.object_entity_id)))
                key = (relation.relation_type.value, *pair)
                if key in symmetric_seen:
                    raise ValueError("symmetric relation must be stored only once for the same entity pair")
                symmetric_seen.add(key)

        for uncertainty in self.analysis.uncertainties:
            unknown_observations = set(uncertainty.observation_refs) - observations
            unknown_entities = set(uncertainty.entity_refs) - entities
            unknown_relations = set(uncertainty.relation_refs) - relations
            unknown_human_facts = set(uncertainty.resolved_by_human_fact_refs) - human_facts
            unknown_resolution_observations = set(uncertainty.resolved_by_observation_refs) - observations
            if unknown_observations:
                raise ValueError(
                    f"uncertainty {uncertainty.uncertainty_id} references unknown observations: {sorted(unknown_observations)}"
                )
            if unknown_entities:
                raise ValueError(
                    f"uncertainty {uncertainty.uncertainty_id} references unknown entities: {sorted(unknown_entities)}"
                )
            if unknown_relations:
                raise ValueError(
                    f"uncertainty {uncertainty.uncertainty_id} references unknown relations: {sorted(unknown_relations)}"
                )
            if unknown_human_facts:
                raise ValueError(
                    f"uncertainty {uncertainty.uncertainty_id} references unknown human_facts: {sorted(unknown_human_facts)}"
                )
            if unknown_resolution_observations:
                raise ValueError(
                    f"uncertainty {uncertainty.uncertainty_id} references unknown resolution observations: {sorted(unknown_resolution_observations)}"
                )

        for question in self.questions:
            unknown = set(question.uncertainty_refs) - uncertainties
            if unknown:
                raise ValueError(f"question {question.question_id} references unknown uncertainties: {sorted(unknown)}")
        return self


class Answer(_ContractModel):
    question_id: QuestionId
    answer_state: AnswerState
    value: str | None
    note: str | None

    @model_validator(mode="after")
    def validate_state_value(self) -> "Answer":
        if self.answer_state is AnswerState.UNKNOWN:
            if self.value is not None:
                raise ValueError("UNKNOWN answer requires value=null")
        elif self.value is None or not self.value.strip():
            raise ValueError("ANSWERED answer requires a non-empty string value")
        return self


class HumanAnswersPayload(_ContractModel):
    answers: list[Answer]

    @model_validator(mode="after")
    def unique_question_ids(self) -> "HumanAnswersPayload":
        ids = [answer.question_id for answer in self.answers]
        if len(ids) != len(set(ids)):
            raise ValueError("answers question_id values must be unique")
        return self


class _Envelope(_ContractModel):
    schema_version: Literal[SCHEMA_VERSION]
    project_id: str
    agent_id: str
    agent_display_name: str
    round_id: RoundId
    package_id: str
    created_at: datetime

    @field_validator("project_id", "agent_id", "agent_display_name")
    @classmethod
    def nonempty_identity(cls, value: str, info) -> str:
        return _ensure_nonempty(value, info.field_name)

    @field_validator("package_id")
    @classmethod
    def package_id_format(cls, value: str) -> str:
        return _validate_package_id(value)

    @field_validator("created_at")
    @classmethod
    def created_at_is_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() != timedelta(0):
            raise ValueError("created_at must be ISO 8601 UTC")
        return value


class AnalysisResultMessage(_Envelope):
    message_type: Literal[MessageType.ANALYSIS_RESULT]
    payload: AnalysisResultPayload


class HumanAnswersMessage(_Envelope):
    message_type: Literal[MessageType.HUMAN_ANSWERS]
    payload: HumanAnswersPayload


ExchangeMessage = Annotated[
    AnalysisResultMessage | HumanAnswersMessage,
    Field(discriminator="message_type"),
]
_EXCHANGE_ADAPTER = TypeAdapter(ExchangeMessage)


def _first_validation_reason(exc: Exception) -> str:
    if hasattr(exc, "errors"):
        errors = exc.errors()
        if errors:
            first = errors[0]
            location = ".".join(str(part) for part in first.get("loc", ()))
            message = first.get("msg", "validation error")
            return f"{location}: {message}" if location else message
    return str(exc)


def _parse_analysis_result(document: Any) -> AnalysisResultMessage:
    parsed = _EXCHANGE_ADAPTER.validate_python(document)
    if not isinstance(parsed, AnalysisResultMessage):
        raise ValueError("source document must be an ANALYSIS_RESULT")
    return parsed


def _validate_answers_against_result(
    answers: HumanAnswersMessage,
    source: AnalysisResultMessage,
) -> None:
    for field_name in ("project_id", "agent_id", "round_id", "package_id"):
        if getattr(answers, field_name) != getattr(source, field_name):
            raise ValueError(f"HUMAN_ANSWERS {field_name} must match source ANALYSIS_RESULT")

    questions = {question.question_id: question for question in source.payload.questions}
    for answer in answers.payload.answers:
        question = questions.get(answer.question_id)
        if question is None:
            raise ValueError(f"answer references unknown question {answer.question_id}")
        if answer.answer_state is AnswerState.UNKNOWN:
            if not question.allow_unknown:
                raise ValueError(f"question {answer.question_id} does not allow UNKNOWN")
            continue
        assert answer.value is not None
        if question.answer_type is AnswerType.YES_NO:
            if answer.value not in {"YES", "NO"}:
                raise ValueError(f"YES_NO question {answer.question_id} requires value YES or NO")
        elif question.answer_type is AnswerType.SINGLE_CHOICE:
            allowed = {choice.value for choice in question.choices}
            if answer.value not in allowed:
                raise ValueError(
                    f"SINGLE_CHOICE question {answer.question_id} requires one declared choice value"
                )
        elif not answer.value.strip():
            raise ValueError(f"FREE_TEXT question {answer.question_id} requires non-empty text")


def validate_exchange_v1(
    document: Any,
    *,
    source_analysis_result: Any | None = None,
) -> dict[str, str | None]:
    """Validate one already-loaded V1 exchange document.

    source_analysis_result is optional for intrinsic HUMAN_ANSWERS validation.
    When supplied, question existence and answer-type rules are also enforced.
    """

    try:
        parsed = _EXCHANGE_ADAPTER.validate_python(document)
        if isinstance(parsed, HumanAnswersMessage) and source_analysis_result is not None:
            source = _parse_analysis_result(source_analysis_result)
            _validate_answers_against_result(parsed, source)
    except Exception as exc:
        return {"status": "INVALID", "reason": _first_validation_reason(exc)}

    status = (
        "VALID ANALYSIS_RESULT"
        if isinstance(parsed, AnalysisResultMessage)
        else "VALID HUMAN_ANSWERS"
    )
    return {"status": status, "reason": None}
