"""Conservative geometry-only split policy for human instruction gestures."""
from __future__ import annotations

from dataclasses import dataclass

from .assembly import AssemblyStep
from .brick_model import BrickModel, BrickModelPart
from .catalog import create_m0_brick_catalog


@dataclass(frozen=True)
class SpatialCoherenceDiagnostic:
    """Explain a spatial decision without enlarging the serialized InstructionPlan."""

    consecutive_gaps_studs: tuple[int, ...]
    baseline_gap_studs: int
    split_after_indices: tuple[int, ...]
    bounding_box_studs: tuple[int, int] | None
    explanation: str


@dataclass(frozen=True)
class SpatialCoherenceInstructionPolicy:
    """Split only at clear spatial discontinuities in the existing placement order.

    The metric is the number of empty stud rows/columns between consecutive 2D
    footprints (Chebyshev gap). Contact/overlap therefore has gap 0. For steps
    with 3+ placements, a split is allowed only where a gap is both at least
    ``min_separation_studs`` and strictly larger than the smallest consecutive
    gap in that step. This deliberately detects a discontinuity, not mere size.

    With exactly two placements there is no internal baseline, so an absolute
    separation at the same threshold is sufficient. Unknown footprint geometry
    is handled conservatively as one unsplit gesture.
    """

    brick_model: BrickModel
    min_separation_studs: int = 2

    def __post_init__(self) -> None:
        if self.min_separation_studs < 1:
            raise ValueError("min_separation_studs must be positive")

    def groups_for(self, step: AssemblyStep) -> list[list[str]]:
        diagnostic = self.diagnose(step)
        if not diagnostic.split_after_indices:
            return [list(step.placement_ids)]
        groups: list[list[str]] = []
        start = 0
        for boundary in diagnostic.split_after_indices:
            groups.append(list(step.placement_ids[start:boundary]))
            start = boundary
        groups.append(list(step.placement_ids[start:]))
        return groups

    def diagnose(self, step: AssemblyStep) -> SpatialCoherenceDiagnostic:
        parts_by_id = {part.placement_id: part for part in self.brick_model.parts}
        try:
            footprints = [self._footprint(parts_by_id[pid]) for pid in step.placement_ids]
        except (KeyError, ValueError):
            return SpatialCoherenceDiagnostic(
                consecutive_gaps_studs=(), baseline_gap_studs=0,
                split_after_indices=(), bounding_box_studs=None,
                explanation="footprint geometry unavailable; conservative direct gesture",
            )

        box = self._bounding_box_size(footprints)
        if len(footprints) < 2:
            return SpatialCoherenceDiagnostic((), 0, (), box, "single placement")

        gaps = tuple(
            self._empty_stud_gap(footprints[index], footprints[index + 1])
            for index in range(len(footprints) - 1)
        )
        baseline = min(gaps)
        if len(gaps) == 1:
            boundaries = (1,) if gaps[0] >= self.min_separation_studs else ()
        else:
            boundaries = tuple(
                index + 1
                for index, gap in enumerate(gaps)
                if gap >= self.min_separation_studs and gap > baseline
            )

        if boundaries:
            explanation = (
                f"clear ordered spatial discontinuity: gaps={gaps}, baseline={baseline}, "
                f"split_after={boundaries}"
            )
        elif max(gaps) >= self.min_separation_studs:
            explanation = (
                f"separation exists but no stronger contiguous boundary: gaps={gaps}, "
                f"baseline={baseline}; preserve construction order as one gesture"
            )
        else:
            explanation = f"spatially coherent consecutive footprints: gaps={gaps}"
        return SpatialCoherenceDiagnostic(gaps, baseline, boundaries, box, explanation)

    @staticmethod
    def _footprint(part: BrickModelPart) -> tuple[int, int, int, int]:
        if part.category != "brick":
            raise ValueError("spatial policy currently resolves canonical brick footprints only")
        definition = create_m0_brick_catalog().get(part.part_id)
        width, depth = definition.footprint(part.rotation_quarter_turns)
        return (
            part.x_studs,
            part.x_studs + width - 1,
            part.y_studs,
            part.y_studs + depth - 1,
        )

    @staticmethod
    def _empty_stud_gap(
        left: tuple[int, int, int, int], right: tuple[int, int, int, int]
    ) -> int:
        lx0, lx1, ly0, ly1 = left
        rx0, rx1, ry0, ry1 = right
        dx = max(0, rx0 - lx1 - 1, lx0 - rx1 - 1)
        dy = max(0, ry0 - ly1 - 1, ly0 - ry1 - 1)
        return max(dx, dy)

    @staticmethod
    def _bounding_box_size(
        footprints: list[tuple[int, int, int, int]],
    ) -> tuple[int, int]:
        min_x = min(box[0] for box in footprints)
        max_x = max(box[1] for box in footprints)
        min_y = min(box[2] for box in footprints)
        max_y = max(box[3] for box in footprints)
        return max_x - min_x + 1, max_y - min_y + 1
