"""Physical placement gate for orthogonal LEGO bricks/plates.

A placement is accepted only with catalog geometry, no solid overlap, and
a documented VALID connector to an already accepted lower part. UNKNOWN
connector evidence does not certify support. Ground parts start at z=0.
A separate GeometricPlacementGate permits geometric-only continuity without
connector proof; neither path certifies clutch strength, stability or insertion.
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
    """Strict 060B connector-evidence placement gate (not a strength certificate)."""

    validation_level = "CONNECTOR_EVIDENCE_STRICT"
    connector_validation = "REQUIRED_VALID"
    physical_certification = False

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
            # Shared geometry of potential lower supporting contacts.
            contact_indices = []
            for i, prev in enumerate(self.accepted):
                pw, pl, ph = prev.dimensions()
                if (prev.z + ph == part.z and
                    part.x < prev.x + pw and prev.x < part.x + w and
                    part.y < prev.y + pl and prev.y < part.y + l):
                    contact_indices.append(i)
            self._require_support(part, contact_indices)
        self.accepted.append(part)
        return part

    def _require_support(self, part, contact_indices):
        """Strict 060B rule: ONLY documented VALID connector evidence supports."""
        if not contact_indices:
            raise ValueError("NO_STUD_SUPPORT")
        candidate = _connector_view(part, len(self.accepted))
        contacts = [
            validate_connection(_connector_view(self.accepted[i], i), candidate)
            for i in contact_indices
        ]
        if any(result.status == "VALID" for result in contacts):
            return
        unknown = next((r for r in contacts if r.status == "UNKNOWN"), None)
        if unknown is not None:
            raise ValueError(f"UNKNOWN_CONNECTOR_SUPPORT:{unknown.reason}")
        raise ValueError(f"INVALID_CONNECTOR_SUPPORT:{contacts[0].reason}")


class GeometricPlacementGate(PhysicalPlacementGate):
    """Non-certifying geometry-only gate; connector evidence is NOT evaluated.

    Shares grid/catalog/rotation/collision checks with the strict gate.
    Vertical footprint contact proves only geometric continuity, never clutch.
    """

    validation_level = "GEOMETRY_ONLY"
    connector_validation = "NOT_CHECKED"
    physical_certification = False

    def _require_support(self, part, contact_indices):
        if not contact_indices:
            raise ValueError("NO_STUD_SUPPORT")

def _verify_components(placements, connector_evidence_required):
    """Shared graph traversal; caller explicitly selects evidenced or geometric edges."""
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

    connector_parts = ([_connector_view(p, i) for i, p in enumerate(placements)]
                       if connector_evidence_required else None)
    for i, a in enumerate(placements):
        aw, al, ah = a.dimensions()
        for j in range(i):
            b = placements[j]
            bw, bl, bh = b.dimensions()
            if ((a.z == b.z + bh or b.z == a.z + ah)
                    and a.x < b.x + bw and b.x < a.x + aw
                    and a.y < b.y + bl and b.y < a.y + al
                    and (not connector_evidence_required or
                         validate_connection(connector_parts[i], connector_parts[j]).status == "VALID")):
                join(i, j)
    if len({root(i) for i in range(len(placements))}) != 1:
        raise ValueError("DISCONNECTED_ASSEMBLY")
    return True


def verify_connected(placements):
    """Strict 060B: only VALID connector edges may connect components."""
    return _verify_components(placements, connector_evidence_required=True)


def verify_geometrically_connected(placements):
    """Geometry-only contact graph, no connector-evidence verification."""
    return _verify_components(placements, connector_evidence_required=False)


def build_geometrically(parts):
    """Explicitly non-certifying geometric preflight for orthogonal fixtures."""
    gate = GeometricPlacementGate()
    for part in parts:
        gate.add(part)
    verify_geometrically_connected(gate.accepted)
    return gate


def build(parts):
    gate = PhysicalPlacementGate()
    for part in parts:
        gate.add(part)
    verify_connected(gate.accepted)
    return gate
