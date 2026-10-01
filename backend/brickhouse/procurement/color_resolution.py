"""Conservative architectural-color to purchase-color resolution.

This layer only accepts an architectural color when its normalized text is
already an exact canonical purchase-color key. It deliberately does not perform
nearest-color matching (for example off_white -> white or dark_gray ->
dark_bluish_gray), because that would silently change the photographed house.
"""

from __future__ import annotations

import csv
import re
from io import StringIO
from typing import Literal

from pydantic import BaseModel, Field

from brickhouse.building.models import Appearance

from .colors import ColorCrosswalk, load_color_crosswalk
from .models import CanonicalOrderPackage, OrderLine


ColorSourceKind = Literal[
    "semantic_color",
    "appearance_walls",
    "appearance_roof",
    "appearance_frames",
    "none",
]
ColorResolutionStatus = Literal[
    "resolved_exact_catalog_key",
    "missing_architectural_color",
    "noncanonical_architectural_color",
]


class ColorResolutionLine(BaseModel):
    part_id: str = Field(min_length=1)
    category: str = Field(min_length=1)
    semantic_color: str | None = None
    source_kind: ColorSourceKind
    source_color: str | None = None
    purchase_color_key: str | None = None
    status: ColorResolutionStatus


class PurchaseColorResolutionReport(BaseModel):
    schema_version: str = "0.1"
    total_order_lines: int = Field(ge=0)
    resolved_lines: int = Field(ge=0)
    unresolved_lines: int = Field(ge=0)
    lines: list[ColorResolutionLine]

    @property
    def complete(self) -> bool:
        return self.unresolved_lines == 0

    def purchase_colors(self) -> dict[tuple[str, str | None], str]:
        return {
            (line.part_id, line.semantic_color): line.purchase_color_key
            for line in self.lines
            if line.purchase_color_key is not None
        }


def _normalized_key(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[\s-]+", "_", value)
    value = re.sub(r"_+", "_", value)
    return value.strip("_")


def _architectural_color(
    line: OrderLine,
    appearance: Appearance | None,
) -> tuple[ColorSourceKind, str | None]:
    if line.semantic_color is not None:
        return "semantic_color", line.semantic_color
    if appearance is None:
        return "none", None
    if line.category in {"brick", "plate"} and appearance.walls is not None:
        return "appearance_walls", appearance.walls.color
    if line.category in {"roof_tile", "ridge_tile"} and appearance.roof is not None:
        return "appearance_roof", appearance.roof.color
    if line.category == "window_frame" and appearance.frames is not None:
        return "appearance_frames", appearance.frames.color
    return "none", None


def resolve_purchase_colors_from_appearance(
    package: CanonicalOrderPackage,
    appearance: Appearance | None,
    *,
    color_crosswalk: ColorCrosswalk | None = None,
) -> PurchaseColorResolutionReport:
    """Resolve only exact canonical physical colors; never choose a nearest color."""

    known = (color_crosswalk or load_color_crosswalk()).by_key()
    lines: list[ColorResolutionLine] = []
    resolved = 0

    for line in package.order_lines:
        source_kind, source_color = _architectural_color(line, appearance)
        if source_color is None:
            lines.append(
                ColorResolutionLine(
                    part_id=line.part_id,
                    category=line.category,
                    semantic_color=line.semantic_color,
                    source_kind=source_kind,
                    status="missing_architectural_color",
                )
            )
            continue

        key = _normalized_key(source_color)
        if key not in known:
            lines.append(
                ColorResolutionLine(
                    part_id=line.part_id,
                    category=line.category,
                    semantic_color=line.semantic_color,
                    source_kind=source_kind,
                    source_color=source_color,
                    status="noncanonical_architectural_color",
                )
            )
            continue

        resolved += 1
        lines.append(
            ColorResolutionLine(
                part_id=line.part_id,
                category=line.category,
                semantic_color=line.semantic_color,
                source_kind=source_kind,
                source_color=source_color,
                purchase_color_key=key,
                status="resolved_exact_catalog_key",
            )
        )

    return PurchaseColorResolutionReport(
        total_order_lines=len(package.order_lines),
        resolved_lines=resolved,
        unresolved_lines=len(package.order_lines) - resolved,
        lines=lines,
    )


def color_resolution_csv(report: PurchaseColorResolutionReport) -> str:
    """Render a deterministic audit file suitable for the future download package."""

    buffer = StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow([
        "part_id",
        "category",
        "semantic_color",
        "source_kind",
        "source_color",
        "purchase_color_key",
        "status",
    ])
    for line in report.lines:
        writer.writerow([
            line.part_id,
            line.category,
            line.semantic_color or "",
            line.source_kind,
            line.source_color or "",
            line.purchase_color_key or "",
            line.status,
        ])
    return buffer.getvalue()
