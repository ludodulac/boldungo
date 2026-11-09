"""Public LDraw library specialization for LEGO connector metadata.

Geometry bounds include protrusions such as studs, so connector mating planes must
not be inferred directly from the full mesh AABB extrema.
"""
from __future__ import annotations

from typing import Iterable
from dataclasses import replace
import re

from .core import AABB, Connector, LDrawLibrary as _GeometryLDrawLibrary


class LDrawLibrary(_GeometryLDrawLibrary):
    """LDraw loader with conservative standard Brick/Plate connector inference."""

    def load_part(self, part_id: str):
        definition = super().load_part(part_id)
        if definition.part_id != "30363.dat" or definition.connectors:
            return definition

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
