"""Rebrickable-backed official part/color catalog verification.

This adapter proves that an official part/color combination exists in the LEGO
catalog represented by Rebrickable and preserves the LEGO Element IDs exposed
for that exact part/color combination.

It does not prove that BrickLink, Wobrick, or LEGO Pick a Brick currently has
stock. The API key is supplied at runtime and is never stored in artifacts.
"""

from __future__ import annotations

import json
import time
from collections import defaultdict
from collections.abc import Callable
from urllib.parse import quote
from urllib.request import Request, urlopen

from pydantic import BaseModel, Field

from .availability import (
    PartColorAvailabilityEvidence,
    PartColorAvailabilityRegistry,
)
from .catalog import PartCrosswalk
from .colors import ColorCrosswalk, load_color_crosswalk
from .models import CanonicalOrderPackage


FetchJson = Callable[[str, dict[str, str]], dict]


class LegoElementCandidates(BaseModel):
    part_id: str = Field(min_length=1)
    color_key: str = Field(min_length=1)
    rebrickable_part_num: str = Field(min_length=1)
    rebrickable_color_id: int = Field(ge=0)
    element_ids: list[str]


class RebrickableCatalogResolution(BaseModel):
    schema_version: str = "0.1"
    availability: PartColorAvailabilityRegistry
    element_candidates: list[LegoElementCandidates]

    def candidates_by_pair(self) -> dict[tuple[str, str], LegoElementCandidates]:
        return {
            (item.part_id, item.color_key): item
            for item in self.element_candidates
        }


def _default_fetch_json(url: str, headers: dict[str, str]) -> dict:
    request = Request(url, headers=headers, method="GET")
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def _parse_color_rows(payload: dict, *, part_num: str) -> dict[int, list[str]]:
    """Parse the official v3 part-colors response.

    Current Rebrickable v3 returns top-level color_id and elements for each
    result. A nested color.id fallback is retained only for defensive
    compatibility with older fixtures/clients.
    """

    results = payload.get("results")
    if not isinstance(results, list):
        raise ValueError(
            f"unexpected Rebrickable colors response for part {part_num!r}"
        )

    parsed: dict[int, list[str]] = {}
    for item in results:
        if not isinstance(item, dict):
            continue

        color_id = item.get("color_id")
        if not isinstance(color_id, int):
            legacy_color = item.get("color")
            if isinstance(legacy_color, dict) and isinstance(legacy_color.get("id"), int):
                color_id = legacy_color["id"]
            else:
                continue

        raw_elements = item.get("elements", [])
        if raw_elements is None:
            raw_elements = []
        if not isinstance(raw_elements, list):
            raise ValueError(
                f"unexpected Rebrickable elements response for part {part_num!r}, "
                f"color {color_id}"
            )
        element_ids = sorted({
            str(element).strip()
            for element in raw_elements
            if str(element).strip()
        })
        parsed[color_id] = element_ids

    return parsed


def resolve_rebrickable_catalog(
    package: CanonicalOrderPackage,
    part_crosswalk: PartCrosswalk,
    *,
    purchase_colors: dict[tuple[str, str | None], str],
    api_key: str,
    color_crosswalk: ColorCrosswalk | None = None,
    fetch_json: FetchJson | None = None,
    request_delay_seconds: float = 1.05,
) -> RebrickableCatalogResolution:
    """Verify requested combinations and preserve exact LEGO Element candidates."""

    if not api_key.strip():
        raise ValueError("Rebrickable API key must be provided at runtime")
    if request_delay_seconds < 0:
        raise ValueError("request_delay_seconds must be >= 0")

    parts = part_crosswalk.by_engine_id()
    colors = (color_crosswalk or load_color_crosswalk()).by_key()
    transport = fetch_json or _default_fetch_json

    requested: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for line in package.order_lines:
        color_key = purchase_colors.get((line.part_id, line.semantic_color))
        if color_key is None:
            continue
        if line.part_id not in parts or color_key not in colors:
            continue
        requested[parts[line.part_id].rebrickable_part_num].append(
            (line.part_id, color_key)
        )

    evidence: list[PartColorAvailabilityEvidence] = []
    candidates: list[LegoElementCandidates] = []
    first = True

    for part_num in sorted(requested):
        if not first and request_delay_seconds:
            time.sleep(request_delay_seconds)
        first = False

        url = (
            "https://rebrickable.com/api/v3/lego/parts/"
            + quote(part_num, safe="")
            + "/colors/?page_size=1000"
        )
        payload = transport(
            url,
            {
                "Authorization": "key " + api_key.strip(),
                "Accept": "application/json",
                "User-Agent": "Boldungo-Procurement/0.1",
            },
        )
        available = _parse_color_rows(payload, part_num=part_num)

        for engine_id, color_key in requested[part_num]:
            color_id = colors[color_key].rebrickable_color_id
            if color_id not in available:
                continue

            evidence.append(
                PartColorAvailabilityEvidence(
                    route="bricklink",
                    part_id=engine_id,
                    color_key=color_key,
                    status="catalog_supported",
                    source=url,
                )
            )
            candidates.append(
                LegoElementCandidates(
                    part_id=engine_id,
                    color_key=color_key,
                    rebrickable_part_num=part_num,
                    rebrickable_color_id=color_id,
                    element_ids=available[color_id],
                )
            )

    candidates.sort(key=lambda item: (item.part_id, item.color_key))
    return RebrickableCatalogResolution(
        availability=PartColorAvailabilityRegistry(evidence=evidence),
        element_candidates=candidates,
    )


def build_bricklink_catalog_availability_from_rebrickable(
    package: CanonicalOrderPackage,
    part_crosswalk: PartCrosswalk,
    *,
    purchase_colors: dict[tuple[str, str | None], str],
    api_key: str,
    color_crosswalk: ColorCrosswalk | None = None,
    fetch_json: FetchJson | None = None,
    request_delay_seconds: float = 1.05,
) -> PartColorAvailabilityRegistry:
    """Backward-compatible convenience wrapper returning catalog evidence only."""

    return resolve_rebrickable_catalog(
        package,
        part_crosswalk,
        purchase_colors=purchase_colors,
        api_key=api_key,
        color_crosswalk=color_crosswalk,
        fetch_json=fetch_json,
        request_delay_seconds=request_delay_seconds,
    ).availability
