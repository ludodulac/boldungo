"""Renderer-neutral human instruction contract derived from AssemblyPlan."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

from pydantic import AliasChoices, BaseModel, Field, model_validator

from .assembly import AssemblyPlan, AssemblyStep, InstructionKind, InstructionView
from .brick_model import BrickModel

InstructionFocus = Literal["normal", "closeup"]
InstructionBoundaryReason = Literal["direct_projection", "pedagogical_split"]


class InstructionStep(BaseModel):
    """One human gesture explaining an ordered slice of one AssemblyStep."""

    step_id: str
    sequence: int = Field(gt=0)
    title: str
    source_assembly_step_id: str
    added_placement_ids: list[str] = Field(
        min_length=1,
        validation_alias=AliasChoices("added_placement_ids", "placement_ids"),
    )
    phase: str
    instruction_kind: InstructionKind = "placement"
    focus: InstructionFocus = "normal"
    view: InstructionView = "perspective"
    boundary_reason: InstructionBoundaryReason = "direct_projection"

    @property
    def placement_ids(self) -> list[str]:
        """Compatibility accessor for code that consumed schema-0.1 objects in memory."""
        return self.added_placement_ids


class InstructionPlan(BaseModel):
    schema_version: str = "0.2"
    building_id: str
    volume_id: str
    total_steps: int = Field(gt=0)
    total_parts: int = Field(gt=0)
    steps: list[InstructionStep] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_structure(self) -> "InstructionPlan":
        if self.total_steps != len(self.steps):
            raise ValueError("total_steps does not match steps length")
        if [step.sequence for step in self.steps] != list(range(1, len(self.steps) + 1)):
            raise ValueError("instruction step sequences must be contiguous from 1")
        ids = [placement_id for step in self.steps for placement_id in step.added_placement_ids]
        if len(ids) != len(set(ids)):
            raise ValueError("instruction plan placement ids must be unique")
        if self.total_parts != len(ids):
            raise ValueError("total_parts does not match referenced placement count")
        return self

    def before_placement_ids(self, sequence: int) -> list[str]:
        """Derive MODEL(n-1) without serializing a duplicate state."""
        self._step_at(sequence)
        return [
            placement_id
            for step in self.steps[: sequence - 1]
            for placement_id in step.added_placement_ids
        ]

    def after_placement_ids(self, sequence: int) -> list[str]:
        """Derive MODEL(n) without serializing a duplicate state."""
        self._step_at(sequence)
        return [
            placement_id
            for step in self.steps[:sequence]
            for placement_id in step.added_placement_ids
        ]

    def _step_at(self, sequence: int) -> InstructionStep:
        if sequence < 1 or sequence > len(self.steps):
            raise IndexError("instruction sequence out of range")
        return self.steps[sequence - 1]


class InstructionSplitPolicy(Protocol):
    """Replaceable policy boundary; it may split, never reorder, an AssemblyStep."""

    def groups_for(self, step: AssemblyStep) -> list[list[str]]: ...


@dataclass(frozen=True)
class DirectInstructionPolicy:
    """Compatibility default: one human gesture per AssemblyStep."""

    def groups_for(self, step: AssemblyStep) -> list[list[str]]:
        return [list(step.placement_ids)]


@dataclass(frozen=True)
class BoundedInstructionSplitPolicy:
    """Temporary deterministic guardrail proving 1->N; not a cognition model.

    The bound is intentionally policy-local and replaceable. Groups are balanced
    contiguous slices so construction order is preserved exactly.
    """

    max_added_placements: int = 3

    def __post_init__(self) -> None:
        if self.max_added_placements < 1:
            raise ValueError("max_added_placements must be positive")

    def groups_for(self, step: AssemblyStep) -> list[list[str]]:
        ids = list(step.placement_ids)
        group_count = (len(ids) + self.max_added_placements - 1) // self.max_added_placements
        if group_count == 1:
            return [ids]
        base, remainder = divmod(len(ids), group_count)
        sizes = [base + (1 if index < remainder else 0) for index in range(group_count)]
        groups: list[list[str]] = []
        cursor = 0
        for size in sizes:
            groups.append(ids[cursor: cursor + size])
            cursor += size
        return groups


def _validate_policy_groups(step: AssemblyStep, groups: list[list[str]]) -> None:
    if not groups or any(not group for group in groups):
        raise ValueError(f"instruction policy emitted an empty split for {step.step_id}")
    flattened = [placement_id for group in groups for placement_id in group]
    if flattened != step.placement_ids:
        raise ValueError(
            f"instruction policy must preserve exact placement order for {step.step_id}"
        )


def validate_instruction_plan_against_assembly(
    instruction_plan: InstructionPlan,
    assembly_plan: AssemblyPlan,
    brick_model: BrickModel | None = None,
) -> None:
    """Prove lossless ordered coverage and, when supplied, BrickModel identity."""
    assembly_by_id = {step.step_id: step for step in assembly_plan.steps}
    emitted_by_source: dict[str, list[str]] = {step.step_id: [] for step in assembly_plan.steps}
    source_order: list[str] = []

    for step in instruction_plan.steps:
        if step.source_assembly_step_id not in assembly_by_id:
            raise ValueError(f"unknown source AssemblyStep {step.source_assembly_step_id!r}")
        emitted_by_source[step.source_assembly_step_id].extend(step.added_placement_ids)
        if not source_order or source_order[-1] != step.source_assembly_step_id:
            source_order.append(step.source_assembly_step_id)

    expected_source_order = [step.step_id for step in assembly_plan.steps]
    if source_order != expected_source_order:
        raise ValueError("InstructionPlan source AssemblySteps must remain contiguous and ordered")

    for source in assembly_plan.steps:
        if emitted_by_source[source.step_id] != source.placement_ids:
            raise ValueError(
                f"InstructionSteps do not preserve exact ordered placements for {source.step_id}"
            )

    expected_ids = [pid for step in assembly_plan.steps for pid in step.placement_ids]
    actual_ids = [pid for step in instruction_plan.steps for pid in step.added_placement_ids]
    if actual_ids != expected_ids:
        raise ValueError("InstructionPlan final state does not match AssemblyPlan")

    if brick_model is not None:
        model_ids = {part.placement_id for part in brick_model.parts}
        unknown = sorted(set(actual_ids) - model_ids)
        missing = sorted(model_ids - set(actual_ids))
        if unknown or missing:
            raise ValueError(
                f"InstructionPlan does not match BrickModel placements: unknown={unknown!r}, missing={missing!r}"
            )


def generate_instruction_plan(
    assembly_plan: AssemblyPlan,
    brick_model: BrickModel | None = None,
    *,
    policy: InstructionSplitPolicy | None = None,
) -> InstructionPlan:
    """Turn admissible AssemblySteps into lossless renderer-neutral human gestures.

    ``DirectInstructionPolicy`` remains the compatibility default. Alternative
    policies may only partition each source step into ordered contiguous gestures;
    they cannot reorder or introduce placements. Physical insertion/support facts
    are deliberately outside this contract.
    """
    resolved_policy = policy or DirectInstructionPolicy()
    steps: list[InstructionStep] = []

    for source in assembly_plan.steps:
        groups = resolved_policy.groups_for(source)
        _validate_policy_groups(source, groups)
        split = len(groups) > 1
        for index, group in enumerate(groups, start=1):
            step_id = source.step_id if not split else f"{source.step_id}:instruction-{index:02d}"
            title = source.title if not split else f"{source.title} · geste {index}/{len(groups)}"
            steps.append(InstructionStep(
                step_id=step_id,
                sequence=len(steps) + 1,
                title=title,
                source_assembly_step_id=source.step_id,
                added_placement_ids=group,
                phase=source.phase,
                instruction_kind=source.instruction_kind,
                focus=source.focus,
                view=source.view,
                boundary_reason="pedagogical_split" if split else "direct_projection",
            ))

    plan = InstructionPlan(
        building_id=assembly_plan.building_id,
        volume_id=assembly_plan.volume_id,
        total_steps=len(steps),
        total_parts=assembly_plan.total_parts,
        steps=steps,
    )
    validate_instruction_plan_against_assembly(plan, assembly_plan, brick_model)
    return plan
