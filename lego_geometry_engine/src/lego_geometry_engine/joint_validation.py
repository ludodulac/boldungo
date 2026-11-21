"""Conservative geometric joint evidence; never promote connectors alone to support.

Official LDraw meshes encode studs, cavities, and body surfaces, but a raw
triangle crossing alone does not label which material is actually penetrated.
A recognized stud/anti-stud pair plus COLLISION is therefore INDETERMINATE,
unless the nominal rectangular body envelopes *also* overlap (rejected).
No physical clutch tolerance is inferred or invented here.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from math import sqrt
import re

from .core import AABB, CONTACT_EPS, PartInstance, Relation, check_collision, find_connections, _segment_triangle

_KNOWN_RECTANGULAR = {
    "3005": ("brick", 1, 1, 24),
    "3004": ("brick", 1, 2, 24),
    "3622": ("brick", 1, 3, 24),
    "3010": ("brick", 1, 4, 24),
    "3009": ("brick", 1, 6, 24),
    "3008": ("brick", 1, 8, 24),
    "3003": ("brick", 2, 2, 24),
    "3001": ("brick", 2, 4, 24),
    "3006": ("brick", 2, 10, 24),
    "3811": ("baseplate", 32, 32, 4),
}
_VERDICTS = {"COMPATIBLE_MATING", "FORBIDDEN_COLLISION", "NO_MECHANICAL_LINK", "INDETERMINATE"}


@dataclass(frozen=True)
class PairEvidence:
    verdict: str
    raw_mesh_relation: str
    connector_count: int
    body_overlap: bool | None
    body_a: tuple[float, ...] | None
    body_b: tuple[float, ...] | None
    reason: str

    def to_dict(self):
        return dict(vars(self))


def _body_envelope(part: PartInstance) -> AABB | None:
    """Measured official nominal *body* bbox, excluding stud protrusions.

    Exact LDraw rectangular widths/lengths and nominal body heights only.
    No claims about hollow-wall thickness, slope, or special part geometry.
    """
    definition = part.definition
    stem = definition.part_id.lower().removesuffix(".dat")
    expected = _KNOWN_RECTANGULAR.get(stem)
    if expected is None or not definition.triangles:
        return None
    family, width, length, height = expected
    match = re.search(r"\b(Brick|Plate|Baseplate)\s+(\d+)\s*x\s*(\d+)\b", definition.description, re.I)
    if not match or (match.group(1).lower(),int(match.group(2)),int(match.group(3))) != (family,width,length):
        return None
    low,high=definition.bbox.minimum,definition.bbox.maximum
    if (abs((high[0]-low[0])-20*length)>CONTACT_EPS or
        abs((high[2]-low[2])-20*width)>CONTACT_EPS or
        abs((high[1]-low[1])-(height+4))>CONTACT_EPS):
        return None
    # Only orthogonal, upright transforms: no sloped roof or mirrored geometry.
    m=part.transform.matrix
    if any(abs(m[1][k])>CONTACT_EPS for k in (0,2)) or abs(m[1][1]-1)>CONTACT_EPS:
        return None
    for axis in (0,2):
        if abs(sum(abs(m[axis][k]) for k in (0,2))-1)>CONTACT_EPS:
            return None
        if any(abs(m[axis][k]-round(m[axis][k]))>CONTACT_EPS for k in (0,2)):
            return None
    top=high[1]-height
    corners=[part.transform.point((x,y,z))
             for x,y,z in product((low[0],high[0]),(top,high[1]),(low[2],high[2]))]
    return AABB(tuple(min(c[k] for c in corners) for k in range(3)),
                tuple(max(c[k] for c in corners) for k in range(3)))


def _positive_body_overlap(a: AABB, b: AABB) -> bool:
    return all(min(a.maximum[k],b.maximum[k])-max(a.minimum[k],b.minimum[k])>CONTACT_EPS for k in range(3))


def assess_pair(a: PartInstance,b: PartInstance, *, relation: Relation | None=None,
                connections: list[dict] | None=None) -> PairEvidence:
    """Four-way honest classification with explicit negative witnesses.

    'COMPATIBLE_MATING' is a *nominal geometric* result from official simple
    brick meshes + correctly aligned connectors + no raw mesh collision.
    Mesh COLLISION can NEVER be promoted to contact merely by connectors.
    """
    r=relation if relation is not None else check_collision(a,b)
    con=connections if connections is not None else find_connections(a,b)
    aa,bb=_body_envelope(a),_body_envelope(b)
    overlap=(_positive_body_overlap(aa,bb) if aa is not None and bb is not None else None)
    body_a=tuple(aa.minimum+aa.maximum) if aa else None
    body_b=tuple(bb.minimum+bb.maximum) if bb else None
    def evidence(kind,reason):
        assert kind in _VERDICTS
        return PairEvidence(kind,r.value,len(con),overlap,body_a,body_b,reason)
    if r is Relation.COLLISION:
        if overlap is True:
            return evidence("FORBIDDEN_COLLISION","Raw mesh intersects and verified rectangular nominal bodies overlap in positive volume.")
        if not con:
            return evidence("FORBIDDEN_COLLISION","Raw mesh intersects without any matching stud/cavity connector. No attachment assumed.")
        return evidence("INDETERMINATE","Raw mesh intersects despite aligned connectors; legal stud-in-cavity versus solid penetration not proved. No graph edge.")
    if r is Relation.SEPARATED:
        if con:
            return evidence("INDETERMINATE","Nominal connector aligns but meshes have no surface contact. No fixation demonstrated.")
        return evidence("NO_MECHANICAL_LINK","Separated meshes and no matching connectors.")
    if not con:
        return evidence("NO_MECHANICAL_LINK","Surface-only contact is not a demonstrated LEGO connection.")
    if overlap is True:
        return evidence("INDETERMINATE","Nominal body overlap despite CONTACT result: conservative rejection of attachment.")
    if aa is None or bb is None:
        return evidence("INDETERMINATE","Unsupported geometry family: no verified simple rectangular body test.")
    return evidence("COMPATIBLE_MATING","Official simple-brick meshes contact without crossing; connectors align; nominal bodies do not overlap.")


def first_mesh_crossing(a: PartInstance,b: PartInstance) -> dict:
    """Actual first strict triangle/triangle edge crossing, in world LDraw units.

    Surface crossing != proven solid-volume intersection. No invented radius.
    Called for seven targeted ambiguous pairs only, not on every engine pair.
    """
    if a.bbox.relation(b.bbox) is Relation.SEPARATED:
        return {"kind":"NO_OVERLAPPING_MESH_BOUNDS"}
    triangles_b=[]
    for tri in b.triangles:
        mi=tuple(min(p[k] for p in tri) for k in range(3))
        ma=tuple(max(p[k] for p in tri) for k in range(3))
        triangles_b.append((tri,mi,ma))
    for ta in a.triangles:
        ami=tuple(min(p[k] for p in ta) for k in range(3))
        ama=tuple(max(p[k] for p in ta) for k in range(3))
        for tb,bmi,bma in triangles_b:
            if any(ama[k]<bmi[k]-CONTACT_EPS or bma[k]<ami[k]-CONTACT_EPS for k in range(3)):
                continue
            for tri,other in ((ta,tb),(tb,ta)):
                for idx in range(3):
                    p0,p1=tri[idx],tri[(idx+1)%3]
                    if _segment_triangle(p0,p1,other) is not True:
                        continue
                    # Möller–Trumbore t of this provably strict segment crossing.
                    edge1=tuple(other[1][k]-other[0][k] for k in range(3))
                    edge2=tuple(other[2][k]-other[0][k] for k in range(3))
                    direction=tuple(p1[k]-p0[k] for k in range(3))
                    cross=(direction[1]*edge2[2]-direction[2]*edge2[1],
                           direction[2]*edge2[0]-direction[0]*edge2[2],
                           direction[0]*edge2[1]-direction[1]*edge2[0])
                    determinant=sum(edge1[k]*cross[k] for k in range(3))
                    if abs(determinant)<CONTACT_EPS:continue
                    s=tuple(p0[k]-other[0][k] for k in range(3))
                    q=(s[1]*edge1[2]-s[2]*edge1[1],
                       s[2]*edge1[0]-s[0]*edge1[2],
                       s[0]*edge1[1]-s[1]*edge1[0])
                    t=sum(edge2[k]*q[k] for k in range(3))/determinant
                    point=tuple(p0[k]+t*direction[k] for k in range(3))
                    matches=find_connections(a,b)
                    nearest=min(matches,key=lambda c:(c["position"][0]-point[0])**2+
                                                    (c["position"][2]-point[2])**2) if matches else None
                    return {"kind":"STRICT_MESH_SURFACE_CROSSING",
                            "world_xyz_ldu":list(point),
                            "nearest_mating_connector_xyz_ldu":list(nearest["position"]) if nearest else None,
                            "xz_distance_to_nearest_mating_connector_ldu":
                                sqrt((nearest["position"][0]-point[0])**2+
                                     (nearest["position"][2]-point[2])**2) if nearest else None,
                            "proves_solid_material_overlap":False}
    return {"kind":"NO_STRICT_TRIANGLE_CROSSING_FOUND",
            "note":"Raw collision may be closed-volume containment or numerical degeneracy; no material witness established."}
