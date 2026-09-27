"""Minimal supported-roof-skin capability.

This module owns the generic distinction between a visible roof skin and an
independent orthogonal LEGO support structure.  It deliberately does not model
all roof framing techniques: it validates only the supported skin primitive
needed by the progressive-house prototype.
"""
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Iterable

from pydantic import BaseModel, Field

from .brick_model import BrickModel, BrickModelPart
from .catalog import standard_orthogonal_definitions
from .orthogonal_geometry import orthogonal_bounds


SUPPORTED_ROOF_SKIN_ID = "BRICK_SLOPED_18_2X1X2_3"


@dataclass(frozen=True)
class SupportedRoofSkinDefinition:
    part_id: str
    width_studs: int
    length_studs: int
    height_plates: int
    low_cell_top_rise_plates: int
    high_cell_top_rise_plates: int
    ldraw_id: str


SUPPORTED_ROOF_SKINS = {
    SUPPORTED_ROOF_SKIN_ID: SupportedRoofSkinDefinition(
        part_id=SUPPORTED_ROOF_SKIN_ID,
        width_studs=2,
        length_studs=1,
        height_plates=2,
        low_cell_top_rise_plates=1,
        high_cell_top_rise_plates=2,
        ldraw_id="5404",
    )
}


class SupportedRoofSkinReport(BaseModel):
    skin_placement_ids: list[str] = Field(default_factory=list)
    ridge_placement_ids: list[str] = Field(default_factory=list)
    support_placement_ids: list[str] = Field(default_factory=list)
    unsupported_skin_ids: list[str] = Field(default_factory=list)
    unsupported_ridge_ids: list[str] = Field(default_factory=list)
    disconnected_support_ids: list[str] = Field(default_factory=list)
    skin_envelope_collisions: list[str] = Field(default_factory=list)
    support_components: list[list[str]] = Field(default_factory=list)

    @property
    def skin_to_support_valid(self) -> bool:
        return not self.unsupported_skin_ids

    @property
    def ridge_contact_valid(self) -> bool:
        return not self.unsupported_ridge_ids

    @property
    def support_internal_valid(self) -> bool:
        return not self.disconnected_support_ids

    @property
    def support_to_host_valid(self) -> bool:
        return not self.disconnected_support_ids

    @property
    def collision_valid(self) -> bool:
        return not self.skin_envelope_collisions

    @property
    def valid(self) -> bool:
        return (
            self.skin_to_support_valid
            and self.ridge_contact_valid
            and self.support_internal_valid
            and self.collision_valid
        )


def is_supported_roof_skin_part(part: BrickModelPart) -> bool:
    definition = SUPPORTED_ROOF_SKINS.get(part.part_id)
    if definition is None:
        return False
    return (
        part.component == "roof"
        and part.category == "roof_tile"
        and part.roof_side in {"negative", "positive"}
        and part.width_studs == definition.width_studs
        and part.length_studs == definition.length_studs
        and part.height_plates == definition.height_plates
    )


def _footprint(part: BrickModelPart) -> set[tuple[int, int]]:
    if part.component == "roof" and part.part_id in SUPPORTED_ROOF_SKINS:
        definition = SUPPORTED_ROOF_SKINS[part.part_id]
        width, length = definition.width_studs, definition.length_studs
        if part.rotation_quarter_turns % 2:
            width, length = length, width
    elif (
        part.component == "roof"
        and part.category == "ridge_tile"
        and part.width_studs is not None
        and part.length_studs is not None
    ):
        width, length = part.width_studs, part.length_studs
        if part.rotation_quarter_turns % 2:
            width, length = length, width
    else:
        definition = standard_orthogonal_definitions().get(part.part_id)
        if definition is None:
            return set()
        width, length = definition.footprint(part.rotation_quarter_turns)
    return {
        (part.x_studs + dx, part.y_studs + dy)
        for dx in range(width)
        for dy in range(length)
    }


def _skin_ceiling(part: BrickModelPart, cell: tuple[int, int]) -> int:
    """Integer conservative top envelope for the supported 5404 raster.

    5404 is two studs along the down-slope axis and one stud along the ridge
    axis in the prototype.  The low footprint cell is bounded by one plate
    above the BrickModel base and the high footprint cell by two plates.
    This envelope is intentionally used only for coarse wall/support clearance;
    the LDraw adapter remains the source of exact part geometry.
    """
    definition = SUPPORTED_ROOF_SKINS[part.part_id]
    x, y = cell
    if part.rotation_quarter_turns % 2:
        local = y - part.y_studs
    else:
        local = x - part.x_studs
    if part.roof_side == "negative":
        high = local == definition.width_studs - 1
    else:
        high = local == 0
    rise = (
        definition.high_cell_top_rise_plates
        if high
        else definition.low_cell_top_rise_plates
    )
    return part.z_plates + rise


def _orthogonal_nodes(model: BrickModel, host_ids: set[str]):
    nodes = {}
    for part in model.parts:
        if part.placement_id not in host_ids and part.component != "roof_support":
            continue
        bounds = orthogonal_bounds(part)
        if bounds is not None:
            nodes[part.placement_id] = (part, bounds, _footprint(part))
    return nodes


def _connection_graph(nodes):
    by_bottom: dict[int, list[str]] = defaultdict(list)
    by_top: dict[int, list[str]] = defaultdict(list)
    for pid, (_, bounds, _) in nodes.items():
        by_bottom[bounds.z0].append(pid)
        by_top[bounds.z1].append(pid)

    graph = {pid: set() for pid in nodes}
    for level, lower_ids in by_top.items():
        upper_ids = by_bottom.get(level, [])
        for lower_id in lower_ids:
            lower_fp = nodes[lower_id][2]
            for upper_id in upper_ids:
                if lower_id == upper_id:
                    continue
                if lower_fp.intersection(nodes[upper_id][2]):
                    graph[lower_id].add(upper_id)
                    graph[upper_id].add(lower_id)
    return graph


def _reachable_from_hosts(graph, host_ids: set[str]) -> set[str]:
    roots = [pid for pid in host_ids if pid in graph]
    reached = set(roots)
    queue = deque(roots)
    while queue:
        pid = queue.popleft()
        for neighbor in graph[pid]:
            if neighbor not in reached:
                reached.add(neighbor)
                queue.append(neighbor)
    return reached


def _components(graph) -> list[list[str]]:
    unseen = set(graph)
    out = []
    while unseen:
        start = next(iter(unseen))
        component = set()
        queue = [start]
        while queue:
            pid = queue.pop()
            if pid in component:
                continue
            component.add(pid)
            unseen.discard(pid)
            queue.extend(graph[pid] - component)
        out.append(sorted(component))
    return sorted(out, key=lambda values: (len(values), values))


def _support_top_candidates(nodes, reached: set[str]):
    by_cell: dict[tuple[int, int], list[tuple[int, str]]] = defaultdict(list)
    for pid in reached:
        _, bounds, footprint = nodes[pid]
        for cell in footprint:
            by_cell[cell].append((bounds.z1, pid))
    return by_cell


def _skin_supported(part: BrickModelPart, by_cell) -> bool:
    for cell in _footprint(part):
        for top_z, _ in by_cell.get(cell, []):
            if top_z == part.z_plates:
                return True
            if part.component == "roof" and part.part_id in SUPPORTED_ROOF_SKINS:
                if part.z_plates < top_z <= _skin_ceiling(part, cell):
                    return True
    return False


def _ridge_supported(part: BrickModelPart, by_cell) -> bool:
    return any(
        top_z == part.z_plates
        for cell in _footprint(part)
        for top_z, _ in by_cell.get(cell, [])
    )


def _skin_clearance_collisions(model: BrickModel, nodes) -> list[str]:
    """Reject orthogonal material that protrudes through the visible skin envelope."""
    collisions = []
    skins = [part for part in model.parts if is_supported_roof_skin_part(part)]
    for skin in skins:
        skin_fp = _footprint(skin)
        for pid, (_, bounds, fp) in nodes.items():
            overlap = skin_fp.intersection(fp)
            if not overlap:
                continue
            for cell in overlap:
                ceiling = _skin_ceiling(skin, cell)
                if bounds.z1 > ceiling and bounds.z0 < ceiling:
                    collisions.append(f"{skin.placement_id}/{pid}@{cell[0]},{cell[1]}")
                    break
    return sorted(set(collisions))


def analyze_supported_roof_skin(
    model: BrickModel,
    *,
    host_placement_ids: Iterable[str],
) -> SupportedRoofSkinReport:
    host_ids = set(host_placement_ids)
    skin = [part for part in model.parts if is_supported_roof_skin_part(part)]
    ridge = [
        part for part in model.parts
        if part.component == "roof" and part.roof_side == "ridge"
    ]
    support = [part for part in model.parts if part.component == "roof_support"]

    nodes = _orthogonal_nodes(model, host_ids)
    graph = _connection_graph(nodes)
    reached = _reachable_from_hosts(graph, host_ids)
    by_cell = _support_top_candidates(nodes, reached)

    unsupported_skin = [
        part.placement_id for part in skin if not _skin_supported(part, by_cell)
    ]
    unsupported_ridge = [
        part.placement_id for part in ridge if not _ridge_supported(part, by_cell)
    ]
    disconnected_support = [
        part.placement_id
        for part in support
        if part.placement_id not in reached
    ]

    return SupportedRoofSkinReport(
        skin_placement_ids=sorted(part.placement_id for part in skin),
        ridge_placement_ids=sorted(part.placement_id for part in ridge),
        support_placement_ids=sorted(part.placement_id for part in support),
        unsupported_skin_ids=sorted(unsupported_skin),
        unsupported_ridge_ids=sorted(unsupported_ridge),
        disconnected_support_ids=sorted(disconnected_support),
        skin_envelope_collisions=_skin_clearance_collisions(model, nodes),
        support_components=_components(graph),
    )


def validate_supported_roof_skin(
    model: BrickModel,
    *,
    host_placement_ids: Iterable[str],
) -> SupportedRoofSkinReport:
    report = analyze_supported_roof_skin(model, host_placement_ids=host_placement_ids)
    if report.unsupported_skin_ids:
        raise ValueError(
            "roof skin without host/support path: " + ", ".join(report.unsupported_skin_ids)
        )
    if report.unsupported_ridge_ids:
        raise ValueError(
            "ridge without support contact: " + ", ".join(report.unsupported_ridge_ids)
        )
    if report.disconnected_support_ids:
        raise ValueError(
            "roof support disconnected from host: " + ", ".join(report.disconnected_support_ids)
        )
    if report.skin_envelope_collisions:
        raise ValueError(
            "roof skin envelope collision: " + ", ".join(report.skin_envelope_collisions)
        )
    return report
