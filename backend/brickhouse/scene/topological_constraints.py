"""Qualitative multiview constraints that survive before metric materialization."""
from __future__ import annotations
from enum import Enum
from pydantic import BaseModel, Field
from brickhouse.building import Facade
from .models import Evidence

class BoundaryAnchor(str, Enum):
    FACADE_START="facade_start"
    FACADE_END="facade_end"
    BUILDING_CORNER="building_corner"
    OPENING="opening"
    PLATFORM="platform"
    STAIR="stair"

class BoundaryConstraint(BaseModel):
    id: str
    subject_id: str
    subject_edge: str
    anchor: BoundaryAnchor
    facade: Facade | None=None
    target_id: str | None=None
    statement: str=Field(min_length=1)
    evidence: list[Evidence]=Field(default_factory=list)

class RoofPlanPosition(BaseModel):
    object_id: str
    front_back: str
    left_right: str
    statement: str=Field(min_length=1)
    evidence: list[Evidence]=Field(default_factory=list)
