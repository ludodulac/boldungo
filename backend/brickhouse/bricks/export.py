"""Stable JSON export bundle for BrickModel downstream consumers."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from brickhouse.building.models import Appearance

from .assembly import AssemblyPlan
from .bags import BagPlan, generate_bag_plan
from .bom import BillOfMaterials
from .brick_model import BrickModel
from .building_layout import BuildingDiscretizationQuality
from .instructions import InstructionPlan, InstructionSplitPolicy, generate_instruction_plan
from .scale_optimizer import ScaleRecommendation


class PhysicalModelSummary(BaseModel):
    """Approximate real-world size of the generated LEGO model."""

    stud_pitch_mm: float = 8.0
    plate_height_mm: float = 3.2
    width_mm: float = Field(gt=0)
    depth_mm: float = Field(gt=0)
    height_mm: float = Field(gt=0)
    approximate_scale_denominator: float | None = Field(default=None, gt=0)


class BrickExportMetadata(BaseModel):
    generator: Literal["brickhouse-engine"] = "brickhouse-engine"
    coordinate_system: Literal["stud-grid"] = "stud-grid"
    vertical_unit: Literal["plate"] = "plate"
    engine_revision: str | None = None
    discretization_quality: list[BuildingDiscretizationQuality] = Field(default_factory=list)
    scale_recommendation: ScaleRecommendation | None = None
    physical_model: PhysicalModelSummary | None = None


class BrickExportFidelityIssue(BaseModel):
    """Explicit architectural information not faithfully represented by this LEGO export."""

    code: str
    severity: Literal["info", "warning", "blocker"] = "warning"
    message: str
    object_id: str | None = None


ArtifactContractState = Literal["not_available", "available", "contract_verified"]
FidelityLevel = Literal["clear", "degraded", "blocked"]
MechanicalVerificationState = Literal["not_claimed", "verified_in_declared_scope"]


class MechanicalVerificationSummary(BaseModel):
    """Mechanical evidence carried by the export without extrapolating its scope.

    The default deliberately makes no mechanical claim. A positive state may only
    be supplied by a caller that has actually run a named validator over explicitly
    declared scopes; bundle/assembly existence never promotes this state.
    """

    state: MechanicalVerificationState = "not_claimed"
    validator_id: str | None = Field(default=None, min_length=1)
    scopes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_claim_scope(self) -> "MechanicalVerificationSummary":
        if self.state == "not_claimed":
            if self.validator_id is not None or self.scopes:
                raise ValueError("not_claimed mechanical verification must not carry validator/scopes")
            return self
        if self.validator_id is None or not self.scopes:
            raise ValueError("verified mechanical scope requires validator_id and at least one scope")
        if len(self.scopes) != len(set(self.scopes)):
            raise ValueError("mechanical verification scopes must be unique")
        return self


class BrickExportCapabilitySummary(BaseModel):
    """Machine-readable guarantees that are already supported by this export.

    ``contract_verified`` means internal artifact consistency has been checked. It
    does not mean physically buildable, deployed, procured, or validated in real use.
    """

    render_artifact: Literal["available"] = "available"
    bom: ArtifactContractState
    assembly_plan: ArtifactContractState
    instruction_plan: ArtifactContractState
    bag_plan: ArtifactContractState
    fidelity_level: FidelityLevel
    mechanical_verification: MechanicalVerificationSummary = Field(
        default_factory=MechanicalVerificationSummary
    )


def derive_export_capability_summary(
    *,
    assembly_plan: AssemblyPlan | None,
    instruction_plan: InstructionPlan | None,
    bag_plan: BagPlan | None,
    fidelity_issues: list[BrickExportFidelityIssue],
    mechanical_verification: MechanicalVerificationSummary | None = None,
) -> BrickExportCapabilitySummary:
    """Derive capability states without converting availability into stronger proof."""
    if any(issue.severity == "blocker" for issue in fidelity_issues):
        fidelity_level: FidelityLevel = "blocked"
    elif any(issue.severity == "warning" for issue in fidelity_issues):
        fidelity_level = "degraded"
    else:
        fidelity_level = "clear"

    return BrickExportCapabilitySummary(
        bom="contract_verified",
        assembly_plan="contract_verified" if assembly_plan is not None else "not_available",
        instruction_plan="contract_verified" if instruction_plan is not None else "not_available",
        bag_plan="contract_verified" if bag_plan is not None else "not_available",
        fidelity_level=fidelity_level,
        mechanical_verification=mechanical_verification or MechanicalVerificationSummary(),
    )


class BrickExportBundle(BaseModel):
    schema_version: Literal["0.1"] = "0.1"
    building_id: str
    volume_id: str
    metadata: BrickExportMetadata = BrickExportMetadata()
    appearance: Appearance | None = None
    brick_model: BrickModel
    bom: BillOfMaterials
    assembly_plan: AssemblyPlan | None = None
    instruction_plan: InstructionPlan | None = None
    bag_plan: BagPlan | None = None
    fidelity_issues: list[BrickExportFidelityIssue] = Field(default_factory=list)
    # Optional for backward compatibility with existing schema-0.1 serialized bundles.
    # New bundles produced by ``create_export_bundle`` always populate it.
    capability_summary: BrickExportCapabilitySummary | None = None

    @model_validator(mode="after")
    def validate_consistency(self) -> "BrickExportBundle":
        if self.brick_model.building_id != self.building_id:
            raise ValueError("BrickModel building_id does not match export building_id")
        if self.bom.building_id != self.building_id:
            raise ValueError("BOM building_id does not match export building_id")
        if self.brick_model.volume_id != self.volume_id:
            raise ValueError("BrickModel volume_id does not match export volume_id")
        if self.bom.volume_id != self.volume_id:
            raise ValueError("BOM volume_id does not match export volume_id")
        if self.bom.total_parts != len(self.brick_model.parts):
            raise ValueError("BOM total_parts does not match BrickModel part count")
        if self.assembly_plan is not None:
            if self.assembly_plan.building_id != self.building_id:
                raise ValueError("AssemblyPlan building_id does not match export building_id")
            if self.assembly_plan.volume_id != self.volume_id:
                raise ValueError("AssemblyPlan volume_id does not match export volume_id")
            if self.assembly_plan.total_parts != len(self.brick_model.parts):
                raise ValueError("AssemblyPlan total_parts does not match BrickModel part count")
        if self.instruction_plan is not None:
            if self.instruction_plan.building_id != self.building_id:
                raise ValueError("InstructionPlan building_id does not match export building_id")
            if self.instruction_plan.volume_id != self.volume_id:
                raise ValueError("InstructionPlan volume_id does not match export volume_id")
            if self.instruction_plan.total_parts != len(self.brick_model.parts):
                raise ValueError("InstructionPlan total_parts does not match BrickModel part count")
            if self.assembly_plan is not None:
                assembly_ids = [pid for step in self.assembly_plan.steps for pid in step.placement_ids]
                instruction_ids = [pid for step in self.instruction_plan.steps for pid in step.added_placement_ids]
                if instruction_ids != assembly_ids:
                    raise ValueError("InstructionPlan placement ordering does not match AssemblyPlan")
        if self.bag_plan is not None:
            if self.bag_plan.building_id != self.building_id:
                raise ValueError("BagPlan building_id does not match export building_id")
            if self.bag_plan.volume_id != self.volume_id:
                raise ValueError("BagPlan volume_id does not match export volume_id")
            if self.bag_plan.total_parts != len(self.brick_model.parts):
                raise ValueError("BagPlan total_parts does not match BrickModel part count")
            if self.assembly_plan is not None:
                assembly_ids = [pid for step in self.assembly_plan.steps for pid in step.placement_ids]
                bag_ids = [pid for bag in self.bag_plan.bags for pid in bag.placement_ids]
                if bag_ids != assembly_ids:
                    raise ValueError("BagPlan placement ordering does not match AssemblyPlan")
                assembly_step_ids = [step.step_id for step in self.assembly_plan.steps]
                bag_step_ids = [step_id for bag in self.bag_plan.bags for step_id in bag.assembly_step_ids]
                if bag_step_ids != assembly_step_ids:
                    raise ValueError("BagPlan step ordering does not match AssemblyPlan")
        if self.capability_summary is not None:
            expected = derive_export_capability_summary(
                assembly_plan=self.assembly_plan,
                instruction_plan=self.instruction_plan,
                bag_plan=self.bag_plan,
                fidelity_issues=self.fidelity_issues,
                mechanical_verification=self.capability_summary.mechanical_verification,
            )
            if self.capability_summary != expected:
                raise ValueError("capability_summary does not match export artifact/fidelity state")
        return self


def _semantic_color_fidelity_issues(model: BrickModel) -> list[BrickExportFidelityIssue]:
    """Expose preserved architectural colors whose LEGO availability is unresolved.

    BrickHouse currently validates deterministic placement capabilities, not the
    availability of every approved part in every LEGO color. A semantic color is
    therefore useful evidence but must never be presented as a validated physical
    procurement choice until a separate part/color capability registry exists.
    """
    combinations = sorted({
        (part.category, part.semantic_color)
        for part in model.parts
        if part.semantic_color is not None
    })
    return [
        BrickExportFidelityIssue(
            code="lego_color_availability_unvalidated",
            severity="info",
            message=(
                f"Architectural color {semantic_color!r} is preserved for {category} parts, "
                "but BrickHouse has not yet validated that the generated LEGO part/color combinations are physically available."
            ),
        )
        for category, semantic_color in combinations
    ]


def _merge_fidelity_issues(
    supplied: list[BrickExportFidelityIssue] | None,
    generated: list[BrickExportFidelityIssue],
) -> list[BrickExportFidelityIssue]:
    merged: list[BrickExportFidelityIssue] = []
    seen: set[tuple[str, str | None, str]] = set()
    for issue in [*(supplied or []), *generated]:
        key = (issue.code, issue.object_id, issue.message)
        if key in seen:
            continue
        seen.add(key)
        merged.append(issue)
    return merged


def _physical_model_summary(
    model: BrickModel,
    discretization_quality: list[BuildingDiscretizationQuality],
) -> PhysicalModelSummary:
    """Compute physical LEGO dimensions without inventing an architectural scale."""
    scales = {round(report.studs_per_meter, 9) for report in discretization_quality}
    scale_denominator = None
    if len(scales) == 1:
        studs_per_meter = next(iter(scales))
        # One real metre becomes ``studs_per_meter * 8 mm`` in the model.
        scale_denominator = 1000.0 / (studs_per_meter * 8.0)
    return PhysicalModelSummary(
        width_mm=model.width_studs * 8.0,
        depth_mm=model.depth_studs * 8.0,
        height_mm=model.height_plates * 3.2,
        approximate_scale_denominator=scale_denominator,
    )


def create_export_bundle(
    model: BrickModel,
    bom: BillOfMaterials,
    assembly_plan: AssemblyPlan | None = None,
    appearance: Appearance | None = None,
    fidelity_issues: list[BrickExportFidelityIssue] | None = None,
    discretization_quality: list[BuildingDiscretizationQuality] | None = None,
    scale_recommendation: ScaleRecommendation | None = None,
    mechanical_verification: MechanicalVerificationSummary | None = None,
    instruction_policy: InstructionSplitPolicy | None = None,
) -> BrickExportBundle:
    """Create the viewer/export bundle without hiding known architectural losses."""
    resolved_quality = discretization_quality or []
    resolved_fidelity_issues = _merge_fidelity_issues(
        fidelity_issues,
        _semantic_color_fidelity_issues(model),
    )
    instruction_plan = (
        generate_instruction_plan(assembly_plan, model, policy=instruction_policy)
        if assembly_plan is not None
        else None
    )
    bag_plan = generate_bag_plan(assembly_plan) if assembly_plan is not None else None
    capability_summary = derive_export_capability_summary(
        assembly_plan=assembly_plan,
        instruction_plan=instruction_plan,
        bag_plan=bag_plan,
        fidelity_issues=resolved_fidelity_issues,
        mechanical_verification=mechanical_verification,
    )
    return BrickExportBundle(
        building_id=model.building_id,
        volume_id=model.volume_id,
        metadata=BrickExportMetadata(
            discretization_quality=resolved_quality,
            scale_recommendation=scale_recommendation,
            physical_model=_physical_model_summary(model, resolved_quality),
        ),
        appearance=appearance,
        brick_model=model,
        bom=bom,
        assembly_plan=assembly_plan,
        instruction_plan=instruction_plan,
        bag_plan=bag_plan,
        fidelity_issues=resolved_fidelity_issues,
        capability_summary=capability_summary,
    )


def export_bundle_json(bundle: BrickExportBundle, *, indent: int = 2) -> str:
    """Serialize an export bundle as deterministic UTF-8 JSON text."""
    return bundle.model_dump_json(indent=indent, exclude_none=True)
