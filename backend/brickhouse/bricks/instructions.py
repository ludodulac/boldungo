"""Stable instruction contract derived from the deterministic AssemblyPlan."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from .assembly import AssemblyPlan, InstructionKind, InstructionView
from .assembly_planner import PlannerResult, build_autonomous_instruction_steps
from .brick_model import BrickModel

InstructionFocus = Literal["normal", "closeup"]


class InstructionStep(BaseModel):
    step_id: str
    sequence: int = Field(gt=0)
    title: str
    placement_ids: list[str] = Field(min_length=1)
    phase: str
    instruction_kind: InstructionKind = "placement"
    focus: InstructionFocus = "normal"
    view: InstructionView = "perspective"


class InstructionPlan(BaseModel):
    schema_version: str = "0.1"
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
        ids = [placement_id for step in self.steps for placement_id in step.placement_ids]
        if len(ids) != len(set(ids)):
            raise ValueError("instruction plan placement ids must be unique")
        if self.total_parts != len(ids):
            raise ValueError("total_parts does not match referenced placement count")
        return self


def generate_instruction_plan(assembly_plan: AssemblyPlan) -> InstructionPlan:
    """Project construction ordering into a renderer-neutral instruction contract.

    Bag assignment deliberately remains outside this contract. The first slice is
    a lossless projection of the instruction-relevant semantics already approved
    by AssemblyPlan so printable and interactive renderers can migrate without
    changing construction order.
    """
    steps = [
        InstructionStep(
            step_id=step.step_id,
            sequence=step.sequence,
            title=step.title,
            placement_ids=list(step.placement_ids),
            phase=step.phase,
            instruction_kind=step.instruction_kind,
            focus=step.focus,
            view=step.view,
        )
        for step in assembly_plan.steps
    ]
    return InstructionPlan(
        building_id=assembly_plan.building_id,
        volume_id=assembly_plan.volume_id,
        total_steps=assembly_plan.total_steps,
        total_parts=assembly_plan.total_parts,
        steps=steps,
    )


def generate_autonomous_instruction_plan(
    model: BrickModel, result: PlannerResult, *, max_parts: int = 8
) -> InstructionPlan:
    """Adapt an experimental autonomous plan to the stable InstructionPlan contract.

    This does not replace the production AssemblyPlan path; it gives renderers a
    contract-compatible experimental input while planner validation matures.
    """
    autonomous = build_autonomous_instruction_steps(model, result, max_parts=max_parts)
    steps = [
        InstructionStep(
            step_id=f"auto-step-{step.sequence:04d}",
            sequence=step.sequence,
            title=f"Autonomous step {step.sequence}",
            placement_ids=list(step.placement_ids),
            phase="autonomous",
            instruction_kind="placement",
            focus="normal",
            view="perspective",
        )
        for step in autonomous
    ]
    return InstructionPlan(
        building_id=model.building_id,
        volume_id=model.volume_id,
        total_steps=len(steps),
        total_parts=sum(len(step.placement_ids) for step in autonomous),
        steps=steps,
    )
