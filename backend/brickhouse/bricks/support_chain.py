"""Deterministic support-chain audit for orthogonal LEGO wall structures.

A canonical part ID does not by itself define connection semantics. Scene-native
terraces, stairs, chimneys, terrain and glazing may deliberately reuse BRICK_* as a
rendering primitive while belonging to another connection domain. This physical
validity slice owns canonical wall bricks plus validated window *frames*: the latter
are real stud/tube connectors inside a wall opening and may legitimately carry the
masonry course above them. Panes never count as structural support.

Roofs and other facade-detail systems keep their dedicated validators until their
support/connection semantics are explicit.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from pydantic import BaseModel, Field

from .brick_model import BrickModel, BrickModelPart
from .catalog import standard_orthogonal_definitions
from .windows import VALIDATED_WINDOW_ASSEMBLIES


class StandardBrickSupportNode(BaseModel):
    placement_id: str
    z_bottom_plates: int = Field(ge=0)
    z_top_plates: int = Field(gt=0)
    footprint: set[tuple[int, int]]
    supporters: list[str] = Field(default_factory=list)
    reaches_ground: bool = False


class StandardBrickSupportReport(BaseModel):
    audited_placement_ids: list[str] = Field(default_factory=list)
    structural_connector_ids: list[str] = Field(default_factory=list)
    unsupported_placement_ids: list[str] = Field(default_factory=list)
    unsupported_connector_ids: list[str] = Field(default_factory=list)
    nodes: list[StandardBrickSupportNode] = Field(default_factory=list)

    @property
    def valid(self) -> bool:
        return not self.unsupported_placement_ids and not self.unsupported_connector_ids


@dataclass(frozen=True)
class _StructuralPartDefinition:
    width_studs: int
    length_studs: int
    height_plates: int

    def footprint(self, rotation_quarter_turns: int) -> tuple[int, int]:
        if rotation_quarter_turns % 2:
            return self.length_studs, self.width_studs
        return self.width_studs, self.length_studs


def _standard_brick_definitions():
    return standard_orthogonal_definitions()


def _window_frame_definitions() -> dict[str, _StructuralPartDefinition]:
    """Return only validated frames with explicit orthogonal wall dimensions."""
    return {
        assembly.frame_part_id: _StructuralPartDefinition(
            width_studs=1,
            length_studs=assembly.width_studs,
            height_plates=assembly.height_bricks * 3,
        )
        for assembly in VALIDATED_WINDOW_ASSEMBLIES
    }


def _is_orthogonal_wall_brick(part: BrickModelPart, definitions) -> bool:
    return (
        part.component == "wall"
        and part.category in {"brick", "plate"}
        and part.part_id in definitions
    )


def _is_validated_window_frame(part: BrickModelPart, definitions) -> bool:
    return (
        part.component == "facade_detail"
        and part.category == "window_frame"
        and part.part_id in definitions
    )


def _footprint(part: BrickModelPart, definition) -> set[tuple[int, int]]:
    width, length = definition.footprint(part.rotation_quarter_turns)
    return {
        (part.x_studs + dx, part.y_studs + dy)
        for dx in range(width)
        for dy in range(length)
    }


def _wall_structural_datum(model: BrickModel, audited: list[BrickModelPart]) -> int:
    """Return the z datum from which this wall shell must be continuously supported.

    Ordinarily the LEGO wall datum is global z=0. Scene-aware framing can translate
    the complete architectural building upward when observed terrain extends below
    the building's architectural zero. That translation is a coordinate-frame change,
    not evidence that the complete wall shell became physically floating. In that
    specific case, preserve the lowest wall course as the wall's structural datum.

    This does *not* validate the terrain assembly or claim that terrain supports the
    building. It only keeps the local wall-chain invariant scoped to its architectural
    host datum; scene-level host/foundation connectivity remains a separate gate.
    """
    if not audited:
        return 0
    wall_base = min(part.z_plates for part in audited)
    if wall_base == 0:
        return 0
    has_lower_scene_terrain = any(
        part.category == "terrain" and part.z_plates < wall_base
        for part in model.parts
    )
    return wall_base if has_lower_scene_terrain else 0


def analyze_standard_brick_support_chain(model: BrickModel) -> StandardBrickSupportReport:
    """Return a transitive wall-support report without mutating ``model``.

    Canonical orthogonal wall pieces at the wall structural datum are anchors. Higher wall
    pieces require direct stud overlap with a structurally reachable node ending at
    their bottom plane. Validated window frames participate in the same graph because
    they have bottom anti-stud and top stud interfaces and an explicit known height.
    Glass panes are deliberately excluded.
    """
    brick_definitions = _standard_brick_definitions()
    frame_definitions = _window_frame_definitions()
    audited = [
        part for part in model.parts
        if _is_orthogonal_wall_brick(part, brick_definitions)
    ]
    connectors = [
        part for part in model.parts
        if _is_validated_window_frame(part, frame_definitions)
    ]
    structural_datum = _wall_structural_datum(model, audited)

    structural_parts: list[tuple[BrickModelPart, object, bool]] = [
        (part, brick_definitions[part.part_id], False) for part in audited
    ] + [
        (part, frame_definitions[part.part_id], True) for part in connectors
    ]
    structural_parts.sort(key=lambda item: (item[0].z_plates, item[0].placement_id))

    by_top: dict[int, list[StandardBrickSupportNode]] = defaultdict(list)
    nodes: list[StandardBrickSupportNode] = []
    unsupported_bricks: list[str] = []
    unsupported_connectors: list[str] = []

    for part, definition, is_connector in structural_parts:
        footprint = _footprint(part, definition)
        possible_supporters = by_top.get(part.z_plates, [])
        supporting_nodes = [
            node for node in possible_supporters
            if node.footprint.intersection(footprint)
        ]
        supporters = sorted(node.placement_id for node in supporting_nodes)
        reaches_ground = part.z_plates == structural_datum or any(
            node.reaches_ground for node in supporting_nodes
        )
        node = StandardBrickSupportNode(
            placement_id=part.placement_id,
            z_bottom_plates=part.z_plates,
            z_top_plates=part.z_plates + definition.height_plates,
            footprint=footprint,
            supporters=supporters,
            reaches_ground=reaches_ground,
        )
        nodes.append(node)
        by_top[node.z_top_plates].append(node)
        if not reaches_ground:
            target = unsupported_connectors if is_connector else unsupported_bricks
            target.append(part.placement_id)

    return StandardBrickSupportReport(
        audited_placement_ids=sorted(part.placement_id for part in audited),
        structural_connector_ids=sorted(part.placement_id for part in connectors),
        unsupported_placement_ids=sorted(unsupported_bricks),
        unsupported_connector_ids=sorted(unsupported_connectors),
        nodes=nodes,
    )


def validate_standard_brick_support_chain(model: BrickModel) -> None:
    """Reject wall structures without a continuous stud/tube chain to their datum."""
    report = analyze_standard_brick_support_chain(model)
    failures = [
        *report.unsupported_placement_ids,
        *report.unsupported_connector_ids,
    ]
    if failures:
        raise ValueError(
            "BrickModel contains orthogonal wall structure without a continuous stud/tube support chain to its structural datum: "
            + ", ".join(sorted(failures))
        )
