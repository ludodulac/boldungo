"""Physical placement gate for orthogonal LEGO bricks/plates.

A placement is accepted only with catalog geometry, no solid overlap, and
a documented VALID connector to an already accepted lower part. UNKNOWN
connector evidence does not certify support. Ground parts start at z=0.
This module does not certify clutch strength, stability or insertion.
"""
from dataclasses import dataclass
from .brick_model import BrickModelPart
from .catalog import standard_orthogonal_definitions
from .connectors import validate_connection

# Subset of the existing catalog.py, deliberately strict (no made-up pieces).
CATALOG = standard_orthogonal_definitions()

@dataclass(frozen=True)
class Placement:
    part_id: str
    x: int
    y: int
    z: int
    rotation: int = 0

    def dimensions(self):
        definition = CATALOG.get(self.part_id)
        if definition is None:
            raise ValueError("PART_NOT_IN_CANONICAL_CATALOG")
        if self.rotation not in (0, 1, 2, 3):
            raise ValueError("INVALID_ROTATION")
        w, l = definition.footprint(self.rotation)
        return w, l, definition.height_plates

def _connector_view(part: Placement, index: int) -> BrickModelPart:
    """Adapt a catalog-checked Placement to the existing connector contract.

    model_construct avoids adding BrickModel-specific coordinate constraints
    to this pre-existing Placement API; dimensions are checked by add().
    Distinct generated IDs prevent unrelated placements sharing an identity.
    """
    return BrickModelPart.model_construct(
        placement_id=f"physical-placement-{index}",
        part_id=part.part_id, category=CATALOG[part.part_id].category,
        component="roof_support", x_studs=part.x, y_studs=part.y,
        z_plates=part.z, rotation_quarter_turns=part.rotation,
    )

class PhysicalPlacementGate:
    def __init__(self):
        self.accepted = []

    def add(self, part):
        if not isinstance(part, Placement):
            raise TypeError("PLACEMENT_REQUIRED")
        if not all(isinstance(v, int) and not isinstance(v, bool) for v in (part.x, part.y, part.z)):
            raise ValueError("OFF_GRID")
        if part.z < 0:
            raise ValueError("BELOW_GROUND")
        w, l, h = part.dimensions()
        for prev in self.accepted:
            pw, pl, ph = prev.dimensions()
            if (part.x < prev.x + pw and prev.x < part.x + w and
                part.y < prev.y + pl and prev.y < part.y + l and
                part.z < prev.z + ph and prev.z < part.z + h):
                raise ValueError("SOLID_COLLISION")
        if part.z > 0:
            # Only lower studs in this exact plane can support the placement.
            candidate = _connector_view(part, len(self.accepted))
            contacts = []
            for i, prev in enumerate(self.accepted):
                pw, pl, ph = prev.dimensions()
                if (prev.z + ph == part.z and
                    part.x < prev.x + pw and prev.x < part.x + w and
                    part.y < prev.y + pl and prev.y < part.y + l):
                    result = validate_connection(_connector_view(prev, i), candidate)
                    contacts.append(result)
                    if result.status == "VALID":
                        break
            else:
                if not contacts:
                    raise ValueError("NO_STUD_SUPPORT")
                unknown = next((r for r in contacts if r.status == "UNKNOWN"), None)
                if unknown is not None:
                    raise ValueError(f"UNKNOWN_CONNECTOR_SUPPORT:{unknown.reason}")
                raise ValueError(f"INVALID_CONNECTOR_SUPPORT:{contacts[0].reason}")
        self.accepted.append(part)
        return part

def verify_connected(placements):
    """Require one component linked only by documented VALID connections.

    This is a connectivity preflight, not a strength or insertion proof.
    """
    if not placements:
        raise ValueError("EMPTY_ASSEMBLY")
    parent = list(range(len(placements)))

    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def join(i, j):
        parent[root(i)] = root(j)

    connector_parts = [_connector_view(p, i) for i, p in enumerate(placements)]
    for i, a in enumerate(placements):
        aw, al, ah = a.dimensions()
        for j in range(i):
            b = placements[j]
            bw, bl, bh = b.dimensions()
            if ((a.z == b.z + bh or b.z == a.z + ah)
                    and a.x < b.x + bw and b.x < a.x + aw
                    and a.y < b.y + bl and b.y < a.y + al
                    and validate_connection(connector_parts[i], connector_parts[j]).status == "VALID"):
                join(i, j)
    if len({root(i) for i in range(len(placements))}) != 1:
        raise ValueError("DISCONNECTED_ASSEMBLY")
    return True

def build(parts):
    gate = PhysicalPlacementGate()
    for part in parts:
        gate.add(part)
    verify_connected(gate.accepted)
    return gate
