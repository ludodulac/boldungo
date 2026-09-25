"""Capability registry separating known LEGO parts from engine-approved placement.

The processed piece dataset is intentionally richer than the deterministic M0
engine. A part being present in that dataset must never make it eligible for
automatic placement by itself. This module gives downstream optimizers an
explicit staged contract and can audit a generated BrickModel before export.
"""
from __future__ import annotations

import csv
from enum import IntEnum
from fractions import Fraction
from pathlib import Path
from typing import Iterable, TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from .brick_model import BrickModel


class PieceCapabilityStage(IntEnum):
    """Highest capability that BrickHouse has validated for one part."""

    KNOWN = 1
    CANONICAL = 2
    GEOMETRY_VALIDATED = 3
    PLACEMENT_APPROVED = 4
    SPECIAL_TECHNIQUE_APPROVED = 5


class PieceCapability(BaseModel):
    engine_id: str
    name: str
    category: str
    width_studs: float | None = Field(default=None, gt=0)
    length_studs: float | None = Field(default=None, gt=0)
    height_studs: float | None = Field(default=None, gt=0)
    source_dataset_known: bool = False
    stage: PieceCapabilityStage = PieceCapabilityStage.KNOWN
    notes: str | None = None

    @property
    def auto_placeable(self) -> bool:
        return self.stage >= PieceCapabilityStage.PLACEMENT_APPROVED

    @property
    def special_technique_ready(self) -> bool:
        return self.stage >= PieceCapabilityStage.SPECIAL_TECHNIQUE_APPROVED


class PieceCapabilityRegistry(BaseModel):
    schema_version: str = "0.1"
    pieces: list[PieceCapability]

    def get(self, engine_id: str) -> PieceCapability:
        for piece in self.pieces:
            if piece.engine_id == engine_id:
                return piece
        raise KeyError(engine_id)

    def approved_ids(self) -> set[str]:
        return {piece.engine_id for piece in self.pieces if piece.auto_placeable}


def _number(value: str | None) -> float | None:
    if value is None:
        return None
    text = value.strip()
    if not text:
        return None
    if "/" in text:
        return float(Fraction(text))
    return float(text)


def load_piece_master(path: str | Path) -> PieceCapabilityRegistry:
    """Load the processed catalogue at the deliberately conservative KNOWN stage."""

    source = Path(path)
    pieces: list[PieceCapability] = []
    with source.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            pieces.append(
                PieceCapability(
                    engine_id=row["engine_id"],
                    name=row.get("name") or row["engine_id"],
                    category=row.get("category") or "Unknown",
                    width_studs=_number(row.get("width_studs")),
                    length_studs=_number(row.get("length_studs")),
                    height_studs=_number(row.get("height_studs")),
                    source_dataset_known=True,
                    stage=PieceCapabilityStage.KNOWN,
                )
            )
    return PieceCapabilityRegistry(pieces=pieces)


def promote_capabilities(
    registry: PieceCapabilityRegistry,
    engine_ids: Iterable[str],
    *,
    stage: PieceCapabilityStage,
    category: str | None = None,
    notes: str | None = None,
) -> PieceCapabilityRegistry:
    """Return a copy with explicit promotions; never promote unspecified rows."""

    by_id = {piece.engine_id: piece.model_copy(deep=True) for piece in registry.pieces}
    for engine_id in engine_ids:
        existing = by_id.get(engine_id)
        if existing is None:
            by_id[engine_id] = PieceCapability(
                engine_id=engine_id,
                name=engine_id,
                category=category or "Engine canonical",
                source_dataset_known=False,
                stage=stage,
                notes=notes,
            )
            continue
        if stage > existing.stage:
            existing.stage = stage
        if notes:
            existing.notes = notes
    return PieceCapabilityRegistry(pieces=sorted(by_id.values(), key=lambda item: item.engine_id))


def default_piece_master_path() -> Path:
    """Resolve the processed catalogue in both source checkout and deployed app layouts."""

    relative = Path("data") / "processed" / "piece_types_master.csv"
    candidates = (
        Path.cwd() / relative,
        Path(__file__).resolve().parents[3] / relative,
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    tried = ", ".join(str(candidate) for candidate in candidates)
    raise FileNotFoundError(f"BrickHouse piece master not found; tried: {tried}")


def create_current_engine_capability_registry(
    path: str | Path | None = None,
) -> PieceCapabilityRegistry:
    """Build the capability view for the engine that is actually implemented today."""

    from .catalog import create_m0_brick_catalog, create_standard_plate_catalog
    from .roof import create_m0_roof_catalog
    from .windows import VALIDATED_WINDOW_ASSEMBLIES

    registry = load_piece_master(path or default_piece_master_path())

    standard_ids = {brick.id for brick in create_m0_brick_catalog().bricks}
    registry = promote_capabilities(
        registry,
        standard_ids,
        stage=PieceCapabilityStage.PLACEMENT_APPROVED,
        notes="Validated for deterministic orthogonal wall/structure placement.",
    )

    plate_ids = {plate.id for plate in create_standard_plate_catalog().bricks}
    registry = promote_capabilities(
        registry,
        plate_ids,
        stage=PieceCapabilityStage.PLACEMENT_APPROVED,
        notes="Validated canonical 1-plate orthogonal stud/tube geometry.",
    )

    roof_ids = {part.id for part in create_m0_roof_catalog().parts}
    registry = promote_capabilities(
        registry,
        roof_ids,
        stage=PieceCapabilityStage.PLACEMENT_APPROVED,
        notes="Validated by the current deterministic roof placement engine.",
    )

    window_ids = {
        part_id
        for assembly in VALIDATED_WINDOW_ASSEMBLIES
        for part_id in (assembly.frame_part_id, assembly.pane_part_id)
    }
    registry = promote_capabilities(
        registry,
        window_ids,
        stage=PieceCapabilityStage.PLACEMENT_APPROVED,
        category="Windows and Doors",
        notes="Validated only as a matched frame/pane window assembly.",
    )
    return registry


def validate_model_part_capabilities(
    model: "BrickModel",
    registry: PieceCapabilityRegistry,
) -> None:
    """Reject generated parts outside their validated deterministic capabilities.

    Catalogue presence is not sufficient. First enforce that every generated part
    is placement-approved. Then apply the BH-166 physical support invariant to the
    connection domain it actually owns: canonical orthogonal wall bricks. Scene
    decks, stairs, chimneys, terrain, glazing, roofs and special techniques require
    their own explicit support/connection validators rather than borrowing wall
    semantics merely because they reuse a BRICK_* primitive.
    """

    approved = registry.approved_ids()
    unsupported = sorted({part.part_id for part in model.parts if part.part_id not in approved})
    if unsupported:
        raise ValueError(
            "BrickModel contains parts that are not approved for deterministic placement: "
            + ", ".join(unsupported)
        )

    from .orthogonal_geometry import validate_orthogonal_collisions
    from .support_chain import validate_standard_brick_support_chain

    validate_orthogonal_collisions(model)
    validate_standard_brick_support_chain(model)
