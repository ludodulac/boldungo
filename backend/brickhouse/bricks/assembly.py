"""Deterministic practical assembly ordering derived from BrickModel."""

from __future__ import annotations

from collections import defaultdict
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from .brick_model import BrickModel, PartComponent

MAX_PARTS_PER_STEP = 12
InstructionKind = Literal["placement", "subassembly"]
InstructionView = Literal["front", "rear", "left", "right", "perspective"]


class AssemblyStep(BaseModel):
    step_id: str
    sequence: int = Field(gt=0)
    component: PartComponent
    z_plates: int = Field(ge=0)
    title: str
    placement_ids: list[str] = Field(min_length=1)
    phase: str
    bag: int = Field(gt=0)
    instruction_kind: InstructionKind = "placement"
    focus: Literal["normal", "closeup"] = "normal"
    view: InstructionView = "perspective"


class AssemblyPlan(BaseModel):
    schema_version: str = "0.2"
    building_id: str
    volume_id: str
    total_steps: int = Field(gt=0)
    total_parts: int = Field(gt=0)
    total_bags: int = Field(gt=0)
    steps: list[AssemblyStep] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_structure(self) -> "AssemblyPlan":
        if self.total_steps != len(self.steps):
            raise ValueError("total_steps does not match steps length")
        if [step.sequence for step in self.steps] != list(range(1, len(self.steps) + 1)):
            raise ValueError("assembly step sequences must be contiguous from 1")
        ids = [placement_id for step in self.steps for placement_id in step.placement_ids]
        if len(ids) != len(set(ids)):
            raise ValueError("assembly plan placement ids must be unique")
        if self.total_parts != len(ids):
            raise ValueError("total_parts does not match referenced placement count")
        bags = sorted({step.bag for step in self.steps})
        if bags != list(range(1, self.total_bags + 1)):
            raise ValueError("assembly bags must be contiguous from 1")
        return self


def _phase_for_part(part) -> str:
    """Return a construction phase without changing BrickModel's stable component schema."""
    if part.category == "terrain":
        return "Terrain"
    if part.placement_id.startswith(("scene-platform:", "scene-stair:")) or part.category == "timber":
        return "Structures extérieures"
    if part.component == "wall":
        return "Structure"
    if part.component == "roof":
        return "Toiture"
    if part.category in {"window_frame", "window_pane"}:
        return "Fenêtres"
    return "Façades"


def _chunks(items: list[str], size: int = MAX_PARTS_PER_STEP) -> list[list[str]]:
    return [items[index:index + size] for index in range(0, len(items), size)]


def _window_subassemblies(model: BrickModel) -> tuple[list[list[str]], set[str]]:
    """Pair a frame and pane sharing the same final anchor into one mini-build."""
    frames: dict[tuple, list] = defaultdict(list)
    panes: dict[tuple, list] = defaultdict(list)
    for part in model.parts:
        if part.category not in {"window_frame", "window_pane"}:
            continue
        key = (part.facade, part.x_studs, part.y_studs, part.z_plates, part.rotation_quarter_turns)
        (frames if part.category == "window_frame" else panes)[key].append(part)
    result: list[list[str]] = []
    used: set[str] = set()
    for key in sorted(set(frames) & set(panes), key=lambda value: tuple(str(v) for v in value)):
        fs = sorted(frames[key], key=lambda p: p.placement_id)
        ps = sorted(panes[key], key=lambda p: p.placement_id)
        for frame, pane in zip(fs, ps):
            result.append([frame.placement_id, pane.placement_id])
            used.update({frame.placement_id, pane.placement_id})
    return result, used


_PHASE_ORDER = {
    "Terrain": 1,
    "Structure": 2,
    "Structures extérieures": 3,
    "Fenêtres": 4,
    "Façades": 5,
    "Toiture": 6,
}
_FACADE_ORDER = {"front": 0, "right": 1, "rear": 2, "left": 3}
_FACADE_LABEL = {
    "front": "avant",
    "right": "droite",
    "rear": "arrière",
    "left": "gauche",
}


def _bag_for_phase(phase: str) -> int:
    return _PHASE_ORDER[phase]


def _append_grouped_steps(pending: list[dict], parts: list, *, phase: str, title: str, focus: str = "closeup") -> None:
    groups: dict[int, list[str]] = defaultdict(list)
    for part in parts:
        groups[part.z_plates].append(part.placement_id)
    for z in sorted(groups):
        for chunk in _chunks(sorted(groups[z])):
            pending.append(dict(component="facade_detail", z=z, title=f"{title} — niveau {z} plates", ids=chunk, phase=phase, kind="placement", focus=focus))


def _wall_sort_key(part) -> tuple[int, int, str]:
    """Keep each instruction action spatially local and deterministic."""
    facade = part.facade.value
    along = part.x_studs if facade in {"front", "rear"} else part.y_studs
    # Build opposite facades in the same canonical left-to-right walking direction.
    if facade in {"rear", "left"}:
        along = -along
    return (_FACADE_ORDER[facade], along, part.placement_id)


def _instruction_view(placement_ids: list[str], parts_by_id: dict) -> InstructionView:
    """Derive a stable camera side from the actual placements in a step."""
    counts = {facade: 0 for facade in _FACADE_ORDER}
    for placement_id in placement_ids:
        facade = parts_by_id[placement_id].facade
        if facade is not None:
            counts[facade.value] += 1
    maximum = max(counts.values())
    if maximum == 0:
        return "perspective"
    return min(
        (facade for facade, count in counts.items() if count == maximum),
        key=lambda facade: _FACADE_ORDER[facade],
    )


def generate_assembly_plan(model: BrickModel) -> AssemblyPlan:
    """Generate short steps, mini-build windows and semantic construction phases."""
    parts_by_id = {part.placement_id: part for part in model.parts}
    pending: list[dict] = []

    # Site first when a Scene provides a terrain surface.
    _append_grouped_steps(
        pending,
        [part for part in model.parts if _phase_for_part(part) == "Terrain"],
        phase="Terrain",
        title="Terrain",
        focus="normal",
    )

    # Main structural shell: bottom-up. Within each course, keep one facade per
    # action so the viewer/notice camera can stay on a stable, readable side.
    wall_groups: dict[tuple[int, str], list] = defaultdict(list)
    for part in model.parts:
        if part.component == "wall":
            wall_groups[(part.z_plates, part.facade.value)].append(part)
    for z, facade in sorted(
        wall_groups,
        key=lambda key: (key[0], _FACADE_ORDER[key[1]]),
    ):
        ordered = sorted(wall_groups[(z, facade)], key=_wall_sort_key)
        chunks = _chunks([part.placement_id for part in ordered])
        for idx, chunk in enumerate(chunks, start=1):
            title = f"Murs — façade {_FACADE_LABEL[facade]} — niveau {z} plates"
            if len(chunks) > 1:
                title += f" · partie {idx}/{len(chunks)}"
            pending.append(dict(component="wall", z=z, title=title, ids=chunk, phase="Structure", kind="placement", focus="normal"))

    # Scene-aware exterior construction. For the one verified south deck
    # cross-plate, give explicit installation actions in correct Z order:
    # existing post first, plate next (temporarily held), boards last.
    exterior = [part for part in model.parts if _phase_for_part(part) == "Structures extérieures"]
    cross_plate_id = "scene-platform:south-timber-deck-main:hidden-cross-plate:00007-00013"
    target_boards = {
        "scene-platform:south-timber-deck-main:board:" + n
        for n in ("00001", "00007", "00013")
    }
    if any(p.placement_id == cross_plate_id for p in exterior):
        for z in sorted({p.z_plates for p in exterior}):
            level = [p for p in exterior if p.z_plates == z]
            plate = [p for p in level if p.placement_id == cross_plate_id]
            boards = [p for p in level if p.placement_id in target_boards]
            others = [p for p in level if p not in plate and p not in boards]
            if plate:
                _append_grouped_steps(
                    pending, plate, phase="Structures extérieures",
                    title="Terrasse sud — maintenir provisoirement la plaque PLATE_1X6 sous les planches",
                )
            if boards:
                _append_grouped_steps(
                    pending, boards, phase="Structures extérieures",
                    title="Terrasse sud — emboîter les planches 00001, 00007 et 00013 sur la plaque, puis retirer le maintien",
                )
            _append_grouped_steps(
                pending, others, phase="Structures extérieures",
                title="Structures extérieures",
            )
    else:
        _append_grouped_steps(
            pending, exterior, phase="Structures extérieures",
            title="Structures extérieures",
        )

    # Windows: build frame + pane as a mini-assembly before placing it.
    assemblies, used_window_ids = _window_subassemblies(model)
    for index, ids in enumerate(assemblies, start=1):
        z = min(parts_by_id[pid].z_plates for pid in ids)
        pending.append(dict(component="facade_detail", z=z, title=f"Assembler la fenêtre {index}", ids=ids, phase="Fenêtres", kind="subassembly", focus="closeup"))

    # Unpaired window parts remain valid individual placement steps.
    for category, label in (("window_frame", "Cadres de fenêtres"), ("window_pane", "Vitrages")):
        groups: dict[int, list[str]] = defaultdict(list)
        for part in model.parts:
            if part.category == category and part.placement_id not in used_window_ids:
                groups[part.z_plates].append(part.placement_id)
        for z in sorted(groups):
            for chunk in _chunks(sorted(groups[z])):
                pending.append(dict(component="facade_detail", z=z, title=f"{label} — niveau {z} plates", ids=chunk, phase="Fenêtres", kind="placement", focus="closeup"))

    # Other facade details, excluding site/exterior parts already scheduled above.
    detail_groups: dict[int, list[str]] = defaultdict(list)
    for part in model.parts:
        if part.component == "facade_detail" and _phase_for_part(part) == "Façades":
            detail_groups[part.z_plates].append(part.placement_id)
    for z in sorted(detail_groups):
        for chunk in _chunks(sorted(detail_groups[z])):
            pending.append(dict(component="facade_detail", z=z, title=f"Détails de façade — niveau {z} plates", ids=chunk, phase="Façades", kind="placement", focus="closeup"))

    # Roof last, bottom-up.
    roof_groups: dict[int, list[str]] = defaultdict(list)
    for part in model.parts:
        if part.component == "roof":
            roof_groups[part.z_plates].append(part.placement_id)
    for z in sorted(roof_groups):
        chunks = _chunks(sorted(roof_groups[z]))
        for idx, chunk in enumerate(chunks, start=1):
            title = f"Toiture — niveau {z} plates"
            if len(chunks) > 1:
                title += f" · partie {idx}/{len(chunks)}"
            pending.append(dict(component="roof", z=z, title=title, ids=chunk, phase="Toiture", kind="placement", focus="normal"))

    steps: list[AssemblyStep] = []
    for sequence, item in enumerate(pending, start=1):
        phase = item["phase"]
        steps.append(AssemblyStep(
            step_id=f"step-{sequence:04d}", sequence=sequence,
            component=item["component"], z_plates=item["z"], title=item["title"],
            placement_ids=item["ids"], phase=phase, bag=_bag_for_phase(phase),
            instruction_kind=item["kind"], focus=item["focus"],
            view=_instruction_view(item["ids"], parts_by_id),
        ))

    all_model_ids = {part.placement_id for part in model.parts}
    all_plan_ids = {placement_id for step in steps for placement_id in step.placement_ids}
    if all_plan_ids != all_model_ids:
        missing = sorted(all_model_ids - all_plan_ids)
        extra = sorted(all_plan_ids - all_model_ids)
        raise RuntimeError(f"assembly coverage mismatch: missing={missing!r}, extra={extra!r}")

    used_bags = sorted({step.bag for step in steps})
    remap = {old: new for new, old in enumerate(used_bags, start=1)}
    for step in steps:
        step.bag = remap[step.bag]

    return AssemblyPlan(
        building_id=model.building_id, volume_id=model.volume_id,
        total_steps=len(steps), total_parts=len(model.parts), total_bags=len(used_bags), steps=steps,
    )
