"""Public LDraw library specialization for LEGO connector metadata.

Geometry bounds include protrusions such as studs, so connector mating planes must
not be inferred directly from the full mesh AABB extrema.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable
from dataclasses import replace
import re

from .core import AABB, Connector, LDrawLibrary as _GeometryLDrawLibrary


class LDrawLibrary(_GeometryLDrawLibrary):
    """LDraw loader with conservative standard Brick/Plate connector inference."""



    # M031 is opt-in: existing callers use genuine LDraw only, unchanged.
    # The CC BY-SA shadow files are supplied from a pinned EXTERNAL path.
    def __init__(self, root, *, ignore_missing_primitives=False,
                 ldcad_shadow_root=None):
        super().__init__(root, ignore_missing_primitives=ignore_missing_primitives)
        self.ldcad_shadow_root = (Path(ldcad_shadow_root)
                                  if ldcad_shadow_root is not None else None)
        self.ldcad_shadow_status = "DISABLED" if ldcad_shadow_root is None else "UNREAD"

    def load_part(self, part_id: str):
        definition = super().load_part(part_id)
        if definition.part_id != "30363.dat":
            return definition
        if not definition.connectors:
            definition = self._m026_source_proven_upper_studs(definition)
        if self.ldcad_shadow_root is not None and (
            len([c for c in definition.connectors if c.type == "stud"]) == 2
            and not any(c.type == "anti_stud" for c in definition.connectors)
        ):
            females = self._ldcad_30363_females()
            if females:
                definition = replace(
                    definition, connectors=definition.connectors + females
                )
                self._cache[definition.part_id] = definition
        return definition

    def _m026_source_proven_upper_studs(self, definition):
            # M026: two genuine top studs explicitly present in the pinned
            # 30363 -> s/30363s01 -> stud.dat hierarchy. No underside socket
            # is inferred: the varying slope has open stud tubes but LDraw
            # does not document a universally valid anti-stud mating plane.
            #
            # Fail closed on another library revision or an incomplete source:
            # the mesh AABB is NEVER used to invent connector coordinates.
            top = self._resolve("30363.dat")
            sub = self._resolve("s/30363s01.dat")
            stud_primitive = self._resolve("stud.dat")
            if top is None or sub is None or stud_primitive is None:
                return definition
            if not re.fullmatch(r"Slope Brick\s+18\s+4\s*x\s*2",
                                definition.description):
                return definition
            main_lines = {" ".join(line.lower().split())
                          for line in top.read_text(encoding="utf-8").splitlines()}
            sub_lines = {" ".join(line.lower().split())
                         for line in sub.read_text(encoding="utf-8").splitlines()}
            if ("1 16 0 0 0 1 0 0 0 1 0 0 0 1 s\\30363s01.dat"
                    not in main_lines):
                return definition
            if not stud_primitive.read_text(encoding="utf-8").splitlines()[0].strip().lower() == "0 stud":
                return definition
            # Exact, source-proven studs: subpart lines 61 and 62 at x=-10,+10,
            # y=0,z=0, in matrices that keep the stud's vertical axis unchanged.
            expected = (
                "1 16 -10 0 0 0 0 1 0 1 0 -1 0 0 stud.dat",
                "1 16 10 0 0 0 0 1 0 1 0 -1 0 0 stud.dat",
            )
            if any(line not in sub_lines for line in expected):
                return definition
            studs = tuple(
                Connector("stud", (x, 0.0, 0.0), (0, -1, 0),
                          ("anti_stud",), 0.25)
                for x in (-10.0, 10.0)
            )
            enriched = replace(definition, connectors=studs)
            self._cache[definition.part_id] = enriched
            return enriched


    @staticmethod
    def _shadow_snap_fields(line: str) -> dict[str, str]:
        prefix = "0 !LDCAD SNAP_CYL "
        if not line.startswith(prefix):
            raise ValueError("Unsupported LDCad snap meta")
        body = line[len(prefix):]
        fields = re.findall(r"\[([^\[\]]+)\]", body)
        if not fields or re.sub(r"\[[^\[\]]+\]", "", body).strip():
            raise ValueError("Malformed LDCad SNAP_CYL tokens")
        result = {}
        for field in fields:
            if "=" not in field:
                raise ValueError("LDCad field missing =")
            key, value = field.split("=", 1)
            if key in result or key not in {"gender", "caps", "secs", "pos",
                                             "grid", "ori", "id", "ID"}:
                raise ValueError("Duplicate or unknown LDCad field: " + key)
            result[key] = value
        return result

    def _ldcad_30363_females(self) -> tuple[Connector, ...]:
        # Only four published F grids for s/30363s01: no bulk import,
        # no guessing from bbox, no network or third-party content committed.
        if self.ldcad_shadow_root is None:
            return ()
        root = self.ldcad_shadow_root
        paths = [
            root / "parts/s/30363s01.dat",
            root / "parts/3004.dat",
            root / "parts/s/3004s01.dat",
            root / "p/stud.dat",
        ]
        if not all(p.is_file() for p in paths):
            self.ldcad_shadow_status = "FAIL_CLOSED_MISSING_SHADOW"
            return ()
        try:
            text_slope, text_brick, text_sub, text_stud = [
                p.read_text(encoding="utf-8") for p in paths
            ]
            for content in (text_slope, text_brick, text_sub, text_stud):
                if "0 !LICENSE CC BY-SA 4.0" not in content:
                    raise ValueError("Unidentified shadow license")
            # 3004 includes s/3004s01, two genuine stud.dat primitives,
            # and p/stud.dat supplies the complementary male R6x4 profile.
            if "0 !LDCAD SNAP_INCL [ref=s\\3004s01.dat]" not in text_brick:
                raise ValueError("Missing 3004 SNAP_INCL")
            if "0 !LDCAD SNAP_CYL [gender=F]" not in text_sub:
                raise ValueError("Missing 3004 inherited shadow")
            male_meta = [self._shadow_snap_fields(line) for line in
                         text_stud.splitlines()
                         if line.startswith("0 !LDCAD SNAP_CYL ")]
            if len(male_meta) != 1 or any(male_meta[0].get(k) != v for k, v in {
                "gender": "M", "caps": "one", "secs": "R 6 4"
            }.items()):
                raise ValueError("Standard stud male profile not validated")

            source_lines = [line for line in text_slope.splitlines()
                            if line.startswith("0 !LDCAD ")]
            if len(source_lines) != 4 or any(
                not line.startswith("0 !LDCAD SNAP_CYL ") for line in source_lines
            ):
                raise ValueError("30363 must contain exactly four supported SNAP_CYL")
            expected = {0.0: 20.0, -20.0: 14.0,
                        -40.0: 8.0, -60.0: 4.0}
            depths = {}
            output = []
            for line in source_lines:
                fields = self._shadow_snap_fields(line)
                if set(fields) not in (
                    {"gender", "caps", "secs", "pos", "grid"},
                    {"gender", "caps", "secs", "pos", "grid", "ori"},
                ):
                    raise ValueError("Unknown 30363 SNAP_CYL options")
                if fields["gender"] != "F" or fields["caps"] != "one":
                    raise ValueError("Invalid gender or caps")
                secs = fields["secs"].split()
                if len(secs) != 3 or secs[0] != "R":
                    raise ValueError("Unsupported cylinder section")
                radius, depth = float(secs[1]), float(secs[2])
                if radius != 6.0 or depth < 4.0:
                    raise ValueError("Unsupported female radius/depth")
                pos = tuple(float(s) for s in fields["pos"].split())
                if len(pos) != 3 or pos[0] != 0.0 or pos[1] != 24.0:
                    raise ValueError("Unexpected female origin")
                if pos[2] in depths or expected.get(pos[2]) != depth:
                    raise ValueError("Unexpected or duplicated female row")
                depths[pos[2]] = depth
                grid = fields["grid"].split()
                if grid != ["C", "2", "1", "20", "0"]:
                    raise ValueError("Only verified two-site centered X grid supported")
                orientation = tuple(float(x) for x in
                                    fields.get("ori", "1 0 0 0 1 0 0 0 1").split())
                if len(orientation) != 9:
                    raise ValueError("Invalid LDCad ori")
                a, b, c, d, e, f, g, h, i = orientation
                rows = ((a, b, c), (d, e, f), (g, h, i))
                if any(abs(sum(row[k] * row[k] for k in range(3)) - 1) > 1e-8
                       for row in rows):
                    raise ValueError("Nonunit LDCad ori")
                if any(abs(sum(rows[x][k] * rows[y][k] for k in range(3))) > 1e-8
                       for x in range(3) for y in range(x + 1, 3)):
                    raise ValueError("Nonorthogonal LDCad ori")
                determinant = (a*(e*i-f*h) - b*(d*i-f*g) + c*(d*h-e*g))
                if abs(determinant - 1) > 1e-8:
                    raise ValueError("Improper LDCad ori")
                # LDCad's default cylinder axis points -Y. Our existing
                # anti_stud normals point INTO female (+Y), opposite the
                # source's axis, to match genuine male stud -Y in BOLDUNGO.
                for local_x in (-10.0, 10.0):
                    # Grid displacement is rotated by ori, pos is not.
                    v = (local_x, 0.0, 0.0)
                    point = tuple(pos[k] + sum(rows[k][j] * v[j]
                                     for j in range(3)) for k in range(3))
                    inward = tuple(sum(rows[k][j] * (0, 1, 0)[j]
                                   for j in range(3)) for k in range(3))
                    output.append(Connector(
                        "anti_stud", point, inward, ("stud",), 0.25,
                        snap_depth_ldu=depth,
                        metadata_origin="LDCadShadowLibrary@9b1131fb1991f8c0bfc072325e4e12f6271aba35",
                    ))
            if depths != expected or len(output) != 8:
                raise ValueError("Incomplete 30363 female locations")
            if len({connector.position for connector in output}) != 8:
                raise ValueError("Duplicated 30363 female positions")
            self.ldcad_shadow_status = "EIGHT_FEMALE_SNAP_SITES_NOMINAL_ONLY"
            return tuple(output)
        except (OSError, ValueError, UnicodeError) as exc:
            self.ldcad_shadow_status = "FAIL_CLOSED_INVALID_SHADOW:" + str(exc)
            return ()

    def _infer_basic_connectors(self, description: str, bbox: AABB) -> Iterable[Connector]:
        match = re.search(r"\b(Brick|Plate)\s+(\d+)\s*x\s*(\d+)\b", description, re.I)
        if not match:
            return ()

        family = match.group(1).lower()
        width, length = int(match.group(2)), int(match.group(3))
        body_height = 24.0 if family == "brick" else 8.0

        # Canonical LDraw Brick/Plate orientation has the underside at the
        # largest Y coordinate. Studs extend above the body toward negative Y,
        # so the top mating plane is body_bottom_y - nominal body height.
        body_bottom_y = bbox.maximum[1]
        body_top_y = body_bottom_y - body_height

        # LDraw's canonical rectangular brick orientation puts the second
        # description dimension (length) on local X and the first dimension
        # (width) on local Z. Example: 3004 "Brick 1 x 2" spans 40 LDU in X
        # and 20 LDU in Z.
        xs = [(index - (length - 1) / 2) * 20 for index in range(length)]
        zs = [(index - (width - 1) / 2) * 20 for index in range(width)]
        connectors: list[Connector] = []
        for x in xs:
            for z in zs:
                connectors.append(
                    Connector(
                        "stud",
                        (x, body_top_y, z),
                        (0, -1, 0),
                        ("anti_stud",),
                        0.25,
                    )
                )
                connectors.append(
                    Connector(
                        "anti_stud",
                        (x, body_bottom_y, z),
                        (0, 1, 0),
                        ("stud",),
                        0.25,
                    )
                )
        return connectors
