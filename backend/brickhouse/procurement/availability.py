"""Supplier-route-specific part/color availability evidence.

Catalog identity and color identity are stable mappings. Availability is not:
it belongs to a procurement route and may need re-checking. This module keeps
that distinction explicit so BrickLink evidence can never authorize a Wobrick
or LEGO Pick a Brick export.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


SupplierRoute = Literal["bricklink", "wobrick", "gobricks", "lego_pick_a_brick"]
AvailabilityStatus = Literal["catalog_supported", "live_available"]


class PartColorAvailabilityEvidence(BaseModel):
    route: SupplierRoute
    part_id: str = Field(min_length=1)
    color_key: str = Field(min_length=1)
    status: AvailabilityStatus
    source: str = Field(min_length=1)
    available_quantity: int | None = Field(default=None, ge=0)


class PartColorAvailabilityRegistry(BaseModel):
    schema_version: str = "0.2"
    evidence: list[PartColorAvailabilityEvidence]

    @model_validator(mode="after")
    def validate_unique_route_pairs(self) -> "PartColorAvailabilityRegistry":
        keys = [(item.route, item.part_id, item.color_key) for item in self.evidence]
        if len(keys) != len(set(keys)):
            raise ValueError("availability registry route/part/color keys must be unique")
        return self

    def evidence_for(
        self,
        route: SupplierRoute,
        part_id: str,
        color_key: str,
    ) -> PartColorAvailabilityEvidence | None:
        for item in self.evidence:
            if (item.route, item.part_id, item.color_key) == (route, part_id, color_key):
                return item
        return None

    def supports(
        self,
        route: SupplierRoute,
        part_id: str,
        color_key: str,
        *,
        require_live: bool = False,
    ) -> bool:
        item = self.evidence_for(route, part_id, color_key)
        if item is None:
            return False
        if require_live:
            return item.status == "live_available"
        return item.status in {"catalog_supported", "live_available"}
