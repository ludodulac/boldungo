"""Rebrickable-backed official part/color catalog verification.

This adapter proves that an official part/color combination exists in the LEGO
catalog represented by Rebrickable. It does not prove that BrickLink, Wobrick,
or LEGO Pick a Brick currently has stock.

The API key is supplied at runtime and is never stored in procurement artifacts.
"""

from __future__ import annotations

import json
import time
from collections import defaultdict
from collections.abc import Callable
from urllib.parse import quote
from urllib.request import Request, urlopen

from .availability import (
    PartColorAvailabilityEvidence,
    PartColorAvailabilityRegistry,
)
from .catalog import PartCrosswalk
from .colors import ColorCrosswalk, load_color_crosswalk
from .models import CanonicalOrderPackage


FetchJson = Callable[[str, dict[str, str]], dict]


def _default_fetch_json(url: str, headers: dict[str, str]) -> dict:
    request = Request(url, headers=headers, method="GET")
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


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
    """Verify requested physical part/colors against Rebrickable's LEGO catalog.

    Only requested order combinations are checked. One colors endpoint call is
    made per unique Rebrickable part number, not per order line.
    """

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
        results = payload.get("results")
        if not isinstance(results, list):
            raise ValueError(
                f"unexpected Rebrickable colors response for part {part_num!r}"
            )

        available_color_ids: set[int] = set()
        for item in results:
            if not isinstance(item, dict):
                continue
            color = item.get("color")
            if isinstance(color, dict) and isinstance(color.get("id"), int):
                available_color_ids.add(color["id"])

        for engine_id, color_key in requested[part_num]:
            color_id = colors[color_key].rebrickable_color_id
            if color_id in available_color_ids:
                evidence.append(
                    PartColorAvailabilityEvidence(
                        route="bricklink",
                        part_id=engine_id,
                        color_key=color_key,
                        status="catalog_supported",
                        source=url,
                    )
                )

    return PartColorAvailabilityRegistry(evidence=evidence)
