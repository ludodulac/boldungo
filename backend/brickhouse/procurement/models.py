"""Canonical order-package models.

These models deliberately stop before supplier resolution. They conserve every
BrickModel placement and BagPlan assignment so later exporters can translate the
same package to LEGO, BrickLink, GoBricks, or another supplier without changing
construction geometry or bag boundaries.
"""

from __future__ import annotations

from collections import Counter
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from brickhouse.bricks.brick_model import PartCategory


class OrderLine(BaseModel):
    part_id: str = Field(min_length=1)
    category: PartCategory
    semantic_color: str | None = Field(default=None, min_length=1)
    quantity: int = Field(gt=0)

    @property
    def identity(self) -> tuple[str, PartCategory, str | None]:
        return (self.part_id, self.category, self.semantic_color)


class BagOrderManifest(BaseModel):
    bag_number: int = Field(gt=0)
    phases: list[str] = Field(min_length=1)
    assembly_step_ids: list[str] = Field(min_length=1)
    total_parts: int = Field(gt=0)
    lines: list[OrderLine] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_total(self) -> "BagOrderManifest":
        if self.total_parts != sum(line.quantity for line in self.lines):
            raise ValueError("bag total_parts does not match line quantities")
        keys = [line.identity for line in self.lines]
        if len(keys) != len(set(keys)):
            raise ValueError("bag order lines must have unique canonical identities")
        return self


class CanonicalOrderPackage(BaseModel):
    """Exact supplier-independent procurement package for one built volume."""

    schema_version: Literal["0.1"] = "0.1"
    building_id: str
    volume_id: str
    supplier_state: Literal["canonical_only"] = "canonical_only"
    total_parts: int = Field(gt=0)
    unique_part_types: int = Field(gt=0)
    total_bags: int = Field(gt=0)
    order_lines: list[OrderLine] = Field(min_length=1)
    bags: list[BagOrderManifest] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_conservation(self) -> "CanonicalOrderPackage":
        if self.total_parts != sum(line.quantity for line in self.order_lines):
            raise ValueError("order package total_parts does not match order line quantities")

        order_keys = [line.identity for line in self.order_lines]
        if len(order_keys) != len(set(order_keys)):
            raise ValueError("global order lines must have unique canonical identities")
        if self.unique_part_types != len(self.order_lines):
            raise ValueError("unique_part_types does not match order_lines length")

        if [bag.bag_number for bag in self.bags] != list(range(1, self.total_bags + 1)):
            raise ValueError("bag numbers must be contiguous from 1")
        if self.total_parts != sum(bag.total_parts for bag in self.bags):
            raise ValueError("order package total_parts does not match bag totals")

        global_counts = Counter({
            line.identity: line.quantity
            for line in self.order_lines
        })
        bag_counts: Counter[tuple[str, PartCategory, str | None]] = Counter()
        for bag in self.bags:
            for line in bag.lines:
                bag_counts[line.identity] += line.quantity

        if global_counts != bag_counts:
            missing_or_wrong = sorted(
                (
                    identity,
                    global_counts.get(identity, 0),
                    bag_counts.get(identity, 0),
                )
                for identity in set(global_counts) | set(bag_counts)
                if global_counts.get(identity, 0) != bag_counts.get(identity, 0)
            )
            raise ValueError(
                "bag composition does not exactly match global order lines: "
                + repr(missing_or_wrong)
            )
        return self
