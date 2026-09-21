"""Generic architectural constraint solving before metric Scene projection.

This module keeps photo-derived topology/ratios separate from metres.  It is
deliberately house-agnostic: callers provide normalized facade observations and
topological constraints, then ask the solver for a self-consistent normalized
layout.  Metric conversion is a later concern.
"""
from __future__ import annotations
from enum import Enum
from pydantic import BaseModel, Field, model_validator

class ConstraintKind(str, Enum):
    ON_FACADE="on_facade"; ABOVE="above"; BELOW="below"; LEFT_OF="left_of"; RIGHT_OF="right_of"
    APPROX_ALIGNED_X="approx_aligned_x"; TOUCHES="touches"; STARTS_AT="starts_at"; ENDS_AT="ends_at"
    SHARES_EDGE_WITH="shares_edge_with"; CONTIGUOUS_WITH="contiguous_with"; CONNECTS_TO="connects_to"
    HORIZONTAL="horizontal"; INDEPENDENT_GRADE="independent_grade"

class NormalizedRect(BaseModel):
    x0: float=Field(ge=0,le=1); x1: float=Field(ge=0,le=1)
    z0: float=Field(ge=0,le=1); z1: float=Field(ge=0,le=1)
    @model_validator(mode="after")
    def ordered(self):
        if self.x1<=self.x0 or self.z1<=self.z0: raise ValueError("normalized rectangle must have positive extent")
        return self

class ArchitecturalConstraint(BaseModel):
    id:str; kind:ConstraintKind; subject_id:str; object_id:str|None=None
    facade:str|None=None; tolerance:float=Field(default=.04,ge=0,le=.25)
    confidence:float=Field(default=1,ge=0,le=1); statement:str

class ConstraintViolation(BaseModel):
    constraint_id:str; residual:float=Field(ge=0); statement:str

class ConstraintReport(BaseModel):
    satisfied:list[str]=Field(default_factory=list)
    violations:list[ConstraintViolation]=Field(default_factory=list)
    score:float=Field(ge=0,le=1)

def _cx(r): return (r.x0+r.x1)/2
def evaluate_normalized_constraints(rects:dict[str,NormalizedRect], constraints:list[ArchitecturalConstraint])->ConstraintReport:
    ok=[]; bad=[]; total=sum(max(c.confidence,1e-9) for c in constraints); penalty=0.0
    for c in constraints:
        a=rects.get(c.subject_id); b=rects.get(c.object_id) if c.object_id else None
        residual=0.0
        if c.kind is ConstraintKind.ABOVE and a and b: residual=max(0.0,b.z1-a.z0)
        elif c.kind is ConstraintKind.BELOW and a and b: residual=max(0.0,a.z1-b.z0)
        elif c.kind is ConstraintKind.LEFT_OF and a and b: residual=max(0.0,a.x1-b.x0)
        elif c.kind is ConstraintKind.RIGHT_OF and a and b: residual=max(0.0,b.x1-a.x0)
        elif c.kind is ConstraintKind.APPROX_ALIGNED_X and a and b: residual=abs(_cx(a)-_cx(b))
        elif c.kind in {ConstraintKind.TOUCHES,ConstraintKind.STARTS_AT,ConstraintKind.ENDS_AT,ConstraintKind.SHARES_EDGE_WITH,ConstraintKind.CONTIGUOUS_WITH} and a and b:
            residual=min(abs(a.x0-b.x0),abs(a.x0-b.x1),abs(a.x1-b.x0),abs(a.x1-b.x1),abs(a.z0-b.z0),abs(a.z0-b.z1),abs(a.z1-b.z0),abs(a.z1-b.z1))
        elif c.kind in {ConstraintKind.ON_FACADE,ConstraintKind.HORIZONTAL,ConstraintKind.INDEPENDENT_GRADE,ConstraintKind.CONNECTS_TO}:
            residual=0.0
        else: residual=1.0
        if residual<=c.tolerance: ok.append(c.id)
        else:
            bad.append(ConstraintViolation(constraint_id=c.id,residual=residual,statement=c.statement))
            penalty+=c.confidence*min(1.0,residual/max(c.tolerance,1e-6))
    return ConstraintReport(satisfied=ok,violations=bad,score=max(0.0,1.0-penalty/total) if total else 1.0)

def normalized_rect_to_metric(rect:NormalizedRect, *, facade_span:float, wall_height:float)->tuple[float,float,float,float]:
    return rect.x0*facade_span, rect.z0*wall_height, (rect.x1-rect.x0)*facade_span, (rect.z1-rect.z0)*wall_height
