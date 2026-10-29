"""Public LDraw library specialization for LEGO connector metadata.

Geometry bounds include protrusions such as studs, so connector mating planes must
not be inferred directly from the full mesh AABB extrema.
"""
from __future__ import annotations

from typing import Iterable
import re

from .core import AABB, Connector, LDrawLibrary as _GeometryLDrawLibrary


class LDrawLibrary(_GeometryLDrawLibrary):
    """LDraw loader with conservative standard Brick/Plate connector inference."""

    def _infer_basic_connectors(self, description: str, bbox: AABB) -> Iterable[Connector]:
        match = re.search(r"\b(Brick|Plate|Baseplate)\s+(\d+)\s*x\s*(\d+)\b", description, re.I)
        if not match:
            return ()

        family = match.group(1).lower()
        width, length = int(match.group(2)), int(match.group(3))
        # Original LDraw 3811.dat has stud roots at y=0 and its base underside at y=4.
        # A Baseplate is not a regular Plate: it has no anti-stud underside.
        body_height = {"brick": 24.0, "plate": 8.0, "baseplate": 4.0}[family]

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
                if family != "baseplate":
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
