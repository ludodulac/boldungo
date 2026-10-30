from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from functools import cached_property
import math
from pathlib import Path
from typing import Iterable, Sequence

Vec3 = tuple[float, float, float]
Mat4 = tuple[
    tuple[float, float, float, float],
    tuple[float, float, float, float],
    tuple[float, float, float, float],
    tuple[float, float, float, float],
]
Triangle = tuple[Vec3, Vec3, Vec3]

EPS = 1e-7
CONTACT_EPS = 1e-5
CONNECTOR_ALIGNMENT_COS = -0.95
RAY_DIRECTION: Vec3 = (1.0, 0.3713906763541037, 0.127831)


class Relation(str, Enum):
    SEPARATED = "SEPARATED"
    CONTACT = "CONTACT"
    COLLISION = "COLLISION"


@dataclass(frozen=True)
class Transform:
    matrix: Mat4 = (
        (1.0, 0.0, 0.0, 0.0),
        (0.0, 1.0, 0.0, 0.0),
        (0.0, 0.0, 1.0, 0.0),
        (0.0, 0.0, 0.0, 1.0),
    )

    @classmethod
    def translation(cls, x: float = 0, y: float = 0, z: float = 0) -> "Transform":
        return cls(((1, 0, 0, x), (0, 1, 0, y), (0, 0, 1, z), (0, 0, 0, 1)))

    def compose(self, other: "Transform") -> "Transform":
        a, b = self.matrix, other.matrix
        matrix = tuple(
            tuple(sum(a[row][k] * b[k][col] for k in range(4)) for col in range(4))
            for row in range(4)
        )
        return Transform(matrix)  # type: ignore[arg-type]

    def point(self, point: Vec3) -> Vec3:
        x, y, z = point
        matrix = self.matrix
        return (
            matrix[0][0] * x + matrix[0][1] * y + matrix[0][2] * z + matrix[0][3],
            matrix[1][0] * x + matrix[1][1] * y + matrix[1][2] * z + matrix[1][3],
            matrix[2][0] * x + matrix[2][1] * y + matrix[2][2] * z + matrix[2][3],
        )

    def vector(self, vector: Vec3) -> Vec3:
        x, y, z = vector
        matrix = self.matrix
        return (
            matrix[0][0] * x + matrix[0][1] * y + matrix[0][2] * z,
            matrix[1][0] * x + matrix[1][1] * y + matrix[1][2] * z,
            matrix[2][0] * x + matrix[2][1] * y + matrix[2][2] * z,
        )


@dataclass(frozen=True)
class AABB:
    minimum: Vec3
    maximum: Vec3

    def relation(self, other: "AABB", eps: float = CONTACT_EPS) -> Relation:
        touches = False
        for a0, a1, b0, b1 in zip(self.minimum, self.maximum, other.minimum, other.maximum):
            if a1 < b0 - eps or b1 < a0 - eps:
                return Relation.SEPARATED
            if abs(a1 - b0) <= eps or abs(b1 - a0) <= eps:
                touches = True
        return Relation.CONTACT if touches else Relation.COLLISION


@dataclass(frozen=True)
class Connector:
    type: str
    position: Vec3
    orientation: Vec3
    compatibility: tuple[str, ...]
    tolerance: float
    owner_part: str | None = None


@dataclass(frozen=True)
class PartDefinition:
    part_id: str
    triangles: tuple[Triangle, ...]
    bbox: AABB
    description: str = ""
    license: str = ""
    connectors: tuple[Connector, ...] = ()


@dataclass(frozen=True)
class PartInstance:
    instance_id: str
    definition: PartDefinition
    transform: Transform = Transform()
    color: int | str | None = None

    @cached_property
    def triangles(self) -> tuple[Triangle, ...]:
        transform = self.transform
        return tuple(
            (transform.point(a), transform.point(b), transform.point(c))
            for a, b, c in self.definition.triangles
        )

    @cached_property
    def bbox(self) -> AABB:
        points = [point for triangle in self.triangles for point in triangle]
        return AABB(
            tuple(min(point[i] for point in points) for i in range(3)),
            tuple(max(point[i] for point in points) for i in range(3)),
        )  # type: ignore[arg-type]


@dataclass
class AssemblyReport:
    valid: bool
    collisions: list[dict] = field(default_factory=list)
    contacts: list[dict] = field(default_factory=list)
    connections: list[dict] = field(default_factory=list)
    unsupported_parts: list[str] = field(default_factory=list)
    disconnected_components: list[list[str]] = field(default_factory=list)
    indeterminate_pairs: list[dict] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)


class LDrawLibrary:
    def __init__(self, root: str | Path, *, ignore_missing_primitives: bool = False):
        self.root = Path(root)
        self.ignore_missing_primitives = ignore_missing_primitives
        self._cache: dict[str, PartDefinition] = {}

    def _resolve(self, name: str) -> Path | None:
        normalized = name.replace("\\", "/").lower()
        if normalized.startswith("s/"):
            candidates = [self.root / "parts" / normalized]
        elif normalized.startswith("48/") or normalized.startswith("8/"):
            candidates = [self.root / "p" / normalized]
        else:
            candidates = [
                self.root / "parts" / normalized,
                self.root / "p" / normalized,
                self.root / "parts" / "s" / normalized,
            ]
        return next((path for path in candidates if path.exists()), None)

    def load_part(self, part_id: str) -> PartDefinition:
        key = part_id.lower().replace("\\", "/")
        if not key.endswith(".dat"):
            key += ".dat"
        if key in self._cache:
            return self._cache[key]

        path = self._resolve(key)
        if not path:
            raise FileNotFoundError(f"LDraw part not found: {part_id}")

        description = ""
        license_line = ""
        triangles = self._expand(path, Transform(), set())
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("0 ") and not description and not line.startswith(("0 Name:", "0 Author:", "0 !")):
                description = line[2:].strip()
            if line.startswith("0 !LICENSE "):
                license_line = line[len("0 !LICENSE ") :].strip()

        points = [point for triangle in triangles for point in triangle]
        if not points:
            raise ValueError(f"No surface triangles produced for {part_id}")
        bbox = AABB(
            tuple(min(point[i] for point in points) for i in range(3)),
            tuple(max(point[i] for point in points) for i in range(3)),
        )  # type: ignore[arg-type]
        definition = PartDefinition(
            key,
            tuple(triangles),
            bbox,
            description,
            license_line,
            tuple(self._infer_basic_connectors(description, bbox)),
        )
        self._cache[key] = definition
        return definition

    def _expand(self, path: Path, transform: Transform, stack: set[Path]) -> list[Triangle]:
        resolved_path = path.resolve()
        if resolved_path in stack:
            raise ValueError(f"Recursive LDraw reference: {path}")
        stack = stack | {resolved_path}
        output: list[Triangle] = []
        invert_next = False

        for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = raw.strip()
            if not line:
                continue
            tokens = line.split()
            line_type = tokens[0]
            if line_type == "0":
                if line.upper().startswith("0 BFC INVERTNEXT"):
                    invert_next = True
                continue
            if line_type == "1":
                if len(tokens) < 15:
                    continue
                values = list(map(float, tokens[2:14]))
                name = " ".join(tokens[14:])
                x, y, z, a, b, c, d, e, f, g, h, i = values
                local = Transform(((a, b, c, x), (d, e, f, y), (g, h, i, z), (0, 0, 0, 1)))
                reference = self._resolve(name)
                if reference is None:
                    if self.ignore_missing_primitives and path.parent.name.lower() in {"p", "s"}:
                        invert_next = False
                        continue
                    raise FileNotFoundError(f"Missing LDraw reference {name!r} from {path}")
                child = self._expand(reference, transform.compose(local), stack)
                if invert_next:
                    child = [(triangle[0], triangle[2], triangle[1]) for triangle in child]
                output.extend(child)
                invert_next = False
            elif line_type in {"3", "4"}:
                numbers = list(map(float, tokens[2:]))
                points = [
                    transform.point((numbers[index], numbers[index + 1], numbers[index + 2]))
                    for index in range(0, len(numbers), 3)
                ]
                if line_type == "3" and len(points) >= 3:
                    output.append((points[0], points[1], points[2]))
                elif line_type == "4" and len(points) >= 4:
                    output.append((points[0], points[1], points[2]))
                    output.append((points[0], points[2], points[3]))
                invert_next = False
            else:
                invert_next = False
        return output

    def _infer_basic_connectors(self, description: str, bbox: AABB) -> Iterable[Connector]:
        import re

        match = re.search(r"\b(Brick|Plate)\s+(\d+)\s*x\s*(\d+)\b", description, re.I)
        if not match:
            return ()
        width, depth = int(match.group(2)), int(match.group(3))
        minimum_y, maximum_y = bbox.minimum[1], bbox.maximum[1]
        xs = [(index - (width - 1) / 2) * 20 for index in range(width)]
        zs = [(index - (depth - 1) / 2) * 20 for index in range(depth)]
        connectors = []
        for x in xs:
            for z in zs:
                connectors.append(Connector("stud", (x, minimum_y, z), (0, -1, 0), ("anti_stud",), 0.25))
                connectors.append(Connector("anti_stud", (x, maximum_y, z), (0, 1, 0), ("stud",), 0.25))
        return connectors


def instantiate(
    definition: PartDefinition,
    instance_id: str,
    transform: Transform | None = None,
    color=None,
) -> PartInstance:
    return PartInstance(instance_id, definition, transform or Transform(), color)


def _vsub(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _dot(a: Vec3, b: Vec3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a: Vec3, b: Vec3) -> Vec3:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _norm(vector: Vec3) -> float:
    return math.sqrt(_dot(vector, vector))


def _normalized(vector: Vec3) -> Vec3 | None:
    length = _norm(vector)
    if length <= EPS:
        return None
    return (vector[0] / length, vector[1] / length, vector[2] / length)


def _segment_triangle(p0: Vec3, p1: Vec3, triangle: Triangle, eps: float = CONTACT_EPS):
    v0, v1, v2 = triangle
    direction = _vsub(p1, p0)
    edge1 = _vsub(v1, v0)
    edge2 = _vsub(v2, v0)
    h = _cross(direction, edge2)
    determinant = _dot(edge1, h)
    if abs(determinant) < eps:
        return None
    inverse = 1 / determinant
    s = _vsub(p0, v0)
    u = inverse * _dot(s, h)
    if u < -eps or u > 1 + eps:
        return None
    q = _cross(s, edge1)
    v = inverse * _dot(direction, q)
    if v < -eps or u + v > 1 + eps:
        return None
    t = inverse * _dot(edge2, q)
    if not (-eps <= t <= 1 + eps):
        return None
    return eps < t < 1 - eps and u > eps and v > eps and u + v < 1 - eps


def _ray_triangle_distance(origin: Vec3, direction: Vec3, triangle: Triangle, eps: float = CONTACT_EPS) -> float | None:
    v0, v1, v2 = triangle
    edge1 = _vsub(v1, v0)
    edge2 = _vsub(v2, v0)
    h = _cross(direction, edge2)
    determinant = _dot(edge1, h)
    if abs(determinant) <= eps:
        return None
    inverse = 1.0 / determinant
    s = _vsub(origin, v0)
    u = inverse * _dot(s, h)
    if u < -eps or u > 1.0 + eps:
        return None
    q = _cross(s, edge1)
    v = inverse * _dot(direction, q)
    if v < -eps or u + v > 1.0 + eps:
        return None
    distance = inverse * _dot(edge2, q)
    if distance <= eps:
        return None
    return distance


def _point_in_mesh(point: Vec3, triangles: Sequence[Triangle]) -> bool:
    distances = sorted(
        distance
        for triangle in triangles
        if (distance := _ray_triangle_distance(point, RAY_DIRECTION, triangle)) is not None
    )
    unique_distances: list[float] = []
    for distance in distances:
        if not unique_distances or abs(distance - unique_distances[-1]) > CONTACT_EPS:
            unique_distances.append(distance)
    return len(unique_distances) % 2 == 1


def _coplanar(t1: Triangle, t2: Triangle, eps: float = CONTACT_EPS) -> bool:
    n1 = _cross(_vsub(t1[1], t1[0]), _vsub(t1[2], t1[0]))
    n2 = _cross(_vsub(t2[1], t2[0]), _vsub(t2[2], t2[0]))
    length1, length2 = _norm(n1), _norm(n2)
    if length1 < eps or length2 < eps:
        return False
    if _norm(_cross(n1, n2)) > eps * length1 * length2:
        return False
    return abs(_dot(n1, _vsub(t2[0], t1[0]))) <= eps * length1


def _project2d(triangle: Triangle):
    normal = _cross(_vsub(triangle[1], triangle[0]), _vsub(triangle[2], triangle[0]))
    drop = max(range(3), key=lambda i: abs(normal[i]))
    return [tuple(point[i] for i in range(3) if i != drop) for point in triangle]


def _orient(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _seg2(a, b, c, d, eps: float = CONTACT_EPS):
    o1, o2, o3, o4 = _orient(a, b, c), _orient(a, b, d), _orient(c, d, a), _orient(c, d, b)
    return (
        o1 * o2 <= eps
        and o3 * o4 <= eps
        and max(min(a[0], b[0]), min(c[0], d[0])) <= min(max(a[0], b[0]), max(c[0], d[0])) + eps
        and max(min(a[1], b[1]), min(c[1], d[1])) <= min(max(a[1], b[1]), max(c[1], d[1])) + eps
    )


def _point2(point, triangle, eps: float = CONTACT_EPS):
    orientations = [_orient(triangle[i], triangle[(i + 1) % 3], point) for i in range(3)]
    return all(value >= -eps for value in orientations) or all(value <= eps for value in orientations)


def _coplanar_overlap(t1: Triangle, t2: Triangle):
    a, b = _project2d(t1), _project2d(t2)
    return (
        any(_seg2(a[i], a[(i + 1) % 3], b[j], b[(j + 1) % 3]) for i in range(3) for j in range(3))
        or _point2(a[0], b)
        or _point2(b[0], a)
    )


def _tri_intersection_kind(t1: Triangle, t2: Triangle):
    if _coplanar(t1, t2):
        return Relation.CONTACT if _coplanar_overlap(t1, t2) else Relation.SEPARATED
    touched = False
    for triangle, other in ((t1, t2), (t2, t1)):
        for index in range(3):
            hit = _segment_triangle(triangle[index], triangle[(index + 1) % 3], other)
            if hit is True:
                return Relation.COLLISION
            if hit is False:
                touched = True
    return Relation.CONTACT if touched else Relation.SEPARATED


def check_collision(a: PartInstance, b: PartInstance) -> Relation:
    if a.bbox.relation(b.bbox) is Relation.SEPARATED:
        return Relation.SEPARATED
    if a.triangles == b.triangles:
        return Relation.COLLISION

    saw_contact = False
    for triangle_a in a.triangles:
        minimum_a = tuple(min(point[i] for point in triangle_a) for i in range(3))
        maximum_a = tuple(max(point[i] for point in triangle_a) for i in range(3))
        for triangle_b in b.triangles:
            minimum_b = tuple(min(point[i] for point in triangle_b) for i in range(3))
            maximum_b = tuple(max(point[i] for point in triangle_b) for i in range(3))
            if any(
                maximum_a[i] < minimum_b[i] - CONTACT_EPS or maximum_b[i] < minimum_a[i] - CONTACT_EPS
                for i in range(3)
            ):
                continue
            relation = _tri_intersection_kind(triangle_a, triangle_b)
            if relation is Relation.COLLISION:
                return relation
            if relation is Relation.CONTACT:
                saw_contact = True

    # Surface-only intersection tests miss the case where one closed mesh is
    # fully enclosed by another. Test representative vertices in both directions.
    if _point_in_mesh(a.triangles[0][0], b.triangles) or _point_in_mesh(b.triangles[0][0], a.triangles):
        return Relation.COLLISION
    return Relation.CONTACT if saw_contact else Relation.SEPARATED


def find_contacts(a: PartInstance, b: PartInstance):
    if check_collision(a, b) is Relation.CONTACT:
        return [{"part_a": a.instance_id, "part_b": b.instance_id, "type": "surface_contact"}]
    return []


def find_connections(a: PartInstance, b: PartInstance):
    output = []
    for connector_a in a.definition.connectors:
        position_a = a.transform.point(connector_a.position)
        orientation_a = _normalized(a.transform.vector(connector_a.orientation))
        if orientation_a is None:
            continue
        for connector_b in b.definition.connectors:
            if connector_b.type not in connector_a.compatibility:
                continue
            position_b = b.transform.point(connector_b.position)
            if _norm(_vsub(position_a, position_b)) > max(connector_a.tolerance, connector_b.tolerance):
                continue
            orientation_b = _normalized(b.transform.vector(connector_b.orientation))
            if orientation_b is None or _dot(orientation_a, orientation_b) > CONNECTOR_ALIGNMENT_COS:
                continue
            output.append(
                {
                    "part_a": a.instance_id,
                    "part_b": b.instance_id,
                    "type": f"{connector_a.type}:{connector_b.type}",
                    "position": position_a,
                }
            )
    return output


def analyze_assembly(parts: Sequence[PartInstance]) -> AssemblyReport:
    """Use one conservative assembly implementation; never downgrade collision by connector alignment."""
    from .assembly import analyze_assembly as safe_analyze_assembly
    return safe_analyze_assembly(parts)


def transform_from_ldraw(values: Sequence[float]) -> Transform:
    if len(values) != 12:
        raise ValueError("Expected x y z a b c d e f g h i")
    x, y, z, a, b, c, d, e, f, g, h, i = map(float, values)
    return Transform(((a, b, c, x), (d, e, f, y), (g, h, i, z), (0, 0, 0, 1)))


def instance_from_dict(data: dict, library: LDrawLibrary) -> PartInstance:
    part_id = data.get("part_id") or data.get("part") or data.get("ldraw_id")
    if not part_id:
        raise ValueError("part_id is required")
    raw_transform = data.get("transform")
    if raw_transform is None:
        position = data.get("position", [0, 0, 0])
        transform = Transform.translation(*position)
    elif isinstance(raw_transform, list) and len(raw_transform) == 12:
        transform = transform_from_ldraw(raw_transform)
    elif isinstance(raw_transform, list) and len(raw_transform) == 4:
        transform = Transform(tuple(tuple(map(float, row)) for row in raw_transform))  # type: ignore[arg-type]
    else:
        raise ValueError("transform must be 12 LDraw values or 4x4 matrix")
    return instantiate(
        library.load_part(str(part_id)),
        str(data.get("instance_id") or data.get("id") or part_id),
        transform,
        data.get("color"),
    )
