"""Mission A: independent, fail-closed LDraw experiment for stud-stacked 30363 roofs.

Nothing in this module reads or mutates GUIDED-004. It intentionally does not
extend the production BrickModel catalog: the 30363 underside connection is an
EXPERIMENTAL nominal LDraw stud/tube hypothesis, never an N5/N6 certificate.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict, deque
from dataclasses import dataclass
from math import atan, degrees, tan, radians
from pathlib import Path
import json

# Authoritative geometry source: LDraw official 30363.dat -> s/30363s01.dat
# Top studs: local (+/-10,0,0); hollow underside at local Y=24;
# stud4a/stud4s at local Z=-10,-30,-50 (see missions/A/EVIDENCE.md).
LDU_PER_STUD = 20
LDU_PER_PLATE = 8
STANDARD_HEIGHT = 3
RIDGE_ADVANCE = 3            # studs/course; one stud of overlap
RIDGE_RISE = 3               # plates/course; top-stud -> underside plane
OFFICIAL_PARTS = {
    "base": "3811", "brick1x8": "3008", "brick1x6": "3009",
    "brick1x4": "3010", "brick1x3": "3622", "brick1x2": "3004",
    "brick1x1": "3005", "pier2x2": "3003", "beam2x8": "3007",
    "beam2x6": "2456", "beam2x4": "3001", "beam2x2": "3003",
    "slope": "30363", "ridge": "3023b",
}


@dataclass(frozen=True)
class Piece:
    pid: str
    ldraw: str
    role: str
    x: int
    y: int
    z: int       # bottom in plates: top of piece is z + height
    sx: int
    sy: int
    height: int = STANDARD_HEIGHT
    side: str = ""
    step: int = 0

    def footprint(self):
        return {(i, j) for i in range(self.x, self.x + self.sx)
                for j in range(self.y, self.y + self.sy)}

    def top_studs(self):
        if self.role == "slope":
            high_x = self.x + 3 if self.side == "left" else self.x
            return {(high_x, j) for j in range(self.y, self.y + self.sy)}
        return self.footprint()

    def bottom_cavities(self):
        # A nominal candidate, NOT an interference/clutch-force assertion.
        return self.footprint()


def _lengths(total, allowed):
    remaining = total
    while remaining:
        size = next((i for i in allowed if i <= remaining), None)
        if size is None:
            raise ValueError("No genuine brick length fits this course")
        yield size
        remaining -= size


def _shape_parts(width, length, pitch, overhang, wall_courses):
    if width not in (20, 26) or length < 20 or length > 30 or length % 2:
        raise ValueError("A_PROTOTYPE_ENVELOPE_REQUIRES_20_OR_26_BY_20_TO_30_EVEN")
    if not 15 <= pitch <= 25:
        raise ValueError("A_PITCH_REQUEST_OUTSIDE_EXPERIMENTAL_15_TO_25")
    if overhang != 0:
        raise ValueError("A_OVERHANG_NEEDS_INDEPENDENT_CLEARANCE_AND_SUPPORT_PROOF")
    if not 3 <= wall_courses <= 5:
        raise ValueError("A_WALL_COURSES_MUST_BE_3_TO_5")
    n = (width - 2) // 6
    wall_top = wall_courses * STANDARD_HEIGHT
    pieces = [Piece("baseplate", "3811", "base", 0, 0, -1, width, length, 1)]
    stages = defaultdict(list)

    def put(role, x, y, z, sx, sy, h=3, side="", step=0, ldraw=None):
        name = f"{role}-{len(pieces):05d}"
        part = Piece(name, ldraw or OFFICIAL_PARTS[role], role,
                     x, y, z, sx, sy, h, side, step)
        pieces.append(part)
        stages[role].append(name)
        return part

    # Exterior masonry, wall studs maintained course by course.
    for course in range(wall_courses):
        z = course * 3
        for x in (0, width - 1):
            yy = 0
            for run in _lengths(length, (8, 6, 4, 3, 2, 1)):
                put("wall", x, yy, z, 1, run, ldraw=OFFICIAL_PARTS[f"brick1x{run}"])
                yy += run
        for y in (0, length - 1):
            xx = 1
            for run in _lengths(width - 2, (8, 6, 4, 3, 2, 1)):
                put("gablewall", xx, y, z, run, 1, ldraw=OFFICIAL_PARTS[f"brick1x{run}"])
                xx += run

    # Brick gables rise only where they cannot intersect the present roof course.
    for j in range(n - 1):
        trim = 4 + j * 3
        for y in (0, length - 1):
            xx = trim
            for run in _lengths(width - 2 * trim, (8, 6, 4, 3, 2, 1)):
                put("gablewall", xx, y, wall_top + 3 * j,
                    run, 1, ldraw=OFFICIAL_PARTS[f"brick1x{run}"])
                xx += run

    roof_beam_y = tuple(_lengths(length - 2, (8, 6, 4, 2)))
    for j in range(n):
        for side in ("left", "right"):
            x = 3 * j if side == "left" else width - 4 - 3 * j
            purlin_x = x + 1
            z_beam = wall_top - 3 + 3 * j
            yy = 1
            for run in roof_beam_y:
                # Two-stud-wide, genuinely stacked masonry pier under EACH beam.
                post_y = yy + (1 if run >= 4 else 0)
                for level in range(0, z_beam, 3):
                    put("pier", purlin_x, post_y, level, 2, 2, ldraw="3003")
                beam = {8:"3007", 6:"2456", 4:"3001", 2:"3003"}[run]
                put("beam", purlin_x, yy, z_beam, 2, run, ldraw=beam)
                yy += run
            for y in range(0, length, 2):
                put("slope", x, y, wall_top + 3*j, 4, 2,
                    side=side, step=j, ldraw="30363")

    # Studs visible on the TWO high ends of the last left/right slopes
    # lie at x=width/2-1 and x=width/2. A plate 1x2 joins the actual two
    # studs; it does NOT test global stiffness or human insertion.
    ridge_z = wall_top + 3*(n - 1) + 3
    for y in range(length):
        put("ridge", width//2-1, y, ridge_z, 2, 1, 1, ldraw="3023b")

    return pieces, {"width_studs": width, "length_studs": length,
        "requested_pitch_degrees": pitch, "overhang_studs": overhang,
        "wall_courses": wall_courses, "roof_courses_each_side": n,
        "roof_surface_facet_degrees": degrees(atan(20 / 60)),
        "course_step_pitch_degrees": degrees(atan(24 / 60)),
        "ridge_z_plates": ridge_z}


def _audit(parts):
    """Nominal stud-graph and conservative orthogonal-body AABB check only."""
    by_top = defaultdict(list)
    for p in parts:
        if p.role != "base":
            by_top[p.z + p.height].append(p)
    base = parts[0]
    supporters = {"baseplate": []}
    ids = {p.pid for p in parts}
    if len(ids) != len(parts):
        raise AssertionError("A_DUPLICATE_PLACEMENT_ID")
    for p in parts[1:]:
        if p.z == 0:
            sup = [base.pid] if p.bottom_cavities() <= base.top_studs() else []
        else:
            sup = [q.pid for q in by_top[p.z] if q.pid != p.pid
                   and (p.bottom_cavities() & q.top_studs())]
        supporters[p.pid] = sorted(sup)
    reachable = {"baseplate"}
    changed = True
    while changed:
        was = len(reachable)
        reachable.update(p.pid for p in parts if p.pid != base.pid
                         and any(q in reachable for q in supporters[p.pid]))
        changed = len(reachable) != was
    unsupported = sorted(ids - reachable)

    graph = {p.pid: set() for p in parts}
    for pid, parents in supporters.items():
        for par in parents:
            graph[pid].add(par)
            graph[par].add(pid)
    remaining = set(ids)
    components = []
    while remaining:
        seed = min(remaining)
        todo = [seed]
        comp = {seed}
        while todo:
            for other in graph[todo.pop()] - comp:
                comp.add(other)
                todo.append(other)
        remaining.difference_update(comp)
        components.append(len(comp))

    # All body boxes use PLATE-grid bottom/top. This deliberately does
    # not substitute for accurate LDraw mesh/stud insertion analysis.
    collisions = []
    for i, p in enumerate(parts[1:], 1):
        for q in parts[i+1:]:
            if (max(p.x, q.x) < min(p.x+p.sx, q.x+q.sx)
                and max(p.y, q.y) < min(p.y+p.sy, q.y+q.sy)
                and max(p.z, q.z) < min(p.z+p.height, q.z+q.height)):
                collisions.append([p.pid, q.pid])
    roof = [p for p in parts if p.role in ("slope","ridge")]
    return {
        "total_parts": len(parts),
        "roof_parts": len(roof),
        "roof_slope_30363": sum(p.role=="slope" for p in parts),
        "roof_ridge_3023b": sum(p.role=="ridge" for p in parts),
        "unsupported_nominal_parts": unsupported,
        "unsupported_nominal_count": len(unsupported),
        "connected_components_nominal": len(components),
        "component_sizes": sorted(components, reverse=True),
        "orthogonal_body_aabb_collisions": collisions[:40],
        "orthogonal_body_aabb_collision_count": len(collisions),
        "supported_roof_to_baseplate_nominal": sum(p.pid in reachable for p in roof),
        "complete_LDraw_mesh_clearance_proven": False,
        "full_stud_interference_and_insertion_proven": False,
        "mechanical_strength_or_n6_certified": False,
        "stud_interface_provenance": "30363s01 local underside cavity; nominal 3-plate vertical overlap and integer XY matching",
        "graph_supporter_counts": dict(Counter(len(v) for k,v in supporters.items() if k!="baseplate")),
        "bom_ldraw": dict(sorted(Counter(p.ldraw for p in parts).items())),
    }


def _ldraw(parts, width, length, title):
    # The official 3811 baseplate is centered at the LDraw origin.
    # Our geometric house is centered on its 32x32 studs.
    normal = "1 0 0 0 1 0 0 0 1"
    turned = "0 0 1 0 1 0 -1 0 0"
    flipped = "-1 0 0 0 1 0 0 0 -1"
    lines = ["0 " + title, "0 Name: "+title.replace(" ","_")+".ldr",
             "0 // EXPERIMENTAL GEOMETRY ONLY: NO PHYSICAL/N5/N6 CERTIFICATE"]
    for p in parts:
        if p.role == "base":
            lines.append("1 2 0 0 0 " + normal + " 3811.dat")
            continue
        cx = 20*(p.y + p.sy/2 - length/2)
        cz = 20*(p.x + p.sx/2 - width/2)
        cy = -8*(p.z + p.height)
        color = (8 if p.role=="slope" else 0 if p.role=="ridge"
                 else 71 if p.role in ("pier","beam") else 15)
        matrix = normal
        if p.role == "slope":
            matrix = normal if p.side == "left" else flipped
            cz += 30 if p.side == "left" else -30
        elif p.sx > p.sy and p.role not in ("pier",):
            matrix = turned
        numbers = lambda v: str(int(v)) if int(v)==v else f"{v:.4f}"
        lines.append(f"0 // {p.pid} {p.role}")
        lines.append("1 "+str(color)+" "+" ".join(map(numbers,(cx,cy,cz)))+" "+
                     matrix+" "+p.ldraw+".dat")
    return "\n".join(lines)+"\n"


def construct(width, length, pitch=22.0, overhang=0, wall_courses=4):
    parts, geometry = _shape_parts(width, length, pitch, overhang, wall_courses)
    audit = _audit(parts)
    if audit["orthogonal_body_aabb_collision_count"] or audit["unsupported_nominal_count"]:
        raise AssertionError("A_BASIC_CONSTRUCTION_GRAPH_OR_COLLISION_FAILED")
    audit.update(geometry)
    audit.update({
        "body_collision_scope": "orthogonal piece bounding boxes only; studs/tubes excluded",
        "nominal_support_is_not_mechanical_certification": True,
        "LDraw_30363_official_nested_subpart_required": "s/30363s01.dat",
        "stepwise_insertion_checked": False,
        "source_canonical_guided004_modified": False,
        "nominal_build_order": [
            "3811_baseplate", "orthogonal_walls_and_real_gables",
            "grounded_2x2_support_piers", "2x8_2x6_2x4_2x2_purlin_courses",
            "30363_slope_course_0_then_rising_courses",
            "3023b_ridge_plates_bridge_two_real_top_studs",
        ],
    })
    return parts, audit



def _technical_elevation_svg(parts, width, length, title):
    """A visible 2D X/height placement projection, NOT an official mesh render.

    It collapses length into one view (do not infer actual depth overlaps).
    Actual bricks/purlins/piers are each drawn using their exact grid positions.
    30363 roof pieces have schematic wedge top shapes, not mesh certification.
    """
    scale_x, scale_z = 22, 6
    pad_x, pad_y = 60, 42
    top_plates = max(p.z+p.height for p in parts if p.role != "base")+3
    height = pad_y + top_plates*scale_z + 68
    view_w = 2*pad_x + width*scale_x
    colors = {"wall":"#e9d8b7","gablewall":"#d7bf94",
              "pier":"#b5d8e9","beam":"#9dbcaa",
              "slope":"#49385c","ridge":"#be6c90"}
    def xx(x):
        return pad_x + x*scale_x
    def yy(z):
        return pad_y+(top_plates-z)*scale_z
    lines=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{view_w}" height="{height}" viewBox="0 0 {view_w} {height}">',
           '<rect width="100%" height="100%" fill="#fcfbf9"/>',
           f'<text x="20" y="25" font-size="18" font-family="sans-serif" fill="#1f2635">{title} — élévation technique X / hauteur</text>',
           f'<line x1="{xx(0)}" y1="{yy(0)}" x2="{xx(width)}" y2="{yy(0)}" stroke="#485163" stroke-width="3"/>']
    seen=set()
    for p in sorted(parts,key=lambda p:({"wall":0,"gablewall":1,"pier":2,"beam":3,"slope":4,"ridge":5}.get(p.role,6),p.z,p.x)):
        if p.role=="base":
            continue
        key=(p.role,p.x,p.z,p.sx,p.side)
        if key in seen:
            continue
        seen.add(key)
        color=colors[p.role]
        if p.role=="slope":
            if p.side=="left":
                points=[(p.x,p.z),(p.x+4,p.z),(p.x+4,p.z+3),(p.x,p.z+0.5)]
            else:
                points=[(p.x,p.z),(p.x+4,p.z),(p.x+4,p.z+0.5),(p.x,p.z+3)]
            coords=" ".join(f"{xx(x):.1f},{yy(z):.1f}" for x,z in points)
            lines.append(f'<polygon points="{coords}" fill="{color}" stroke="#2a2836" stroke-width="1.2"/>')
        else:
            x,y=xx(p.x),yy(p.z+p.height)
            lines.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{p.sx*scale_x:.1f}" height="{p.height*scale_z:.1f}" fill="{color}" stroke="#6d6573" stroke-width="0.7"/>')
    lines.append(f'<text x="20" y="{height-36}" font-size="12" font-family="sans-serif" fill="#424956">Positions des pièces projetées sur X/hauteur ; la profondeur est aplatie.</text>')
    lines.append(f'<text x="20" y="{height-18}" font-size="12" font-family="sans-serif" fill="#ab345b">NON CERTIFIÉ : vrais maillages, insertion, adhérence et résistance non établis.</text>')
    lines.append('</svg>')
    return "\\n".join(lines)+"\\n"

def main(output):
    output = Path(output)
    output.mkdir(parents=True,exist_ok=True)
    cases = (("A1",20,20,18,3), ("A2",26,24,22,4),
             ("A3",26,28,22,5))
    report = []
    for name, w, length, pitch, wall_courses in cases:
        parts, audit = construct(w, length, pitch=pitch,
                                 overhang=0, wall_courses=wall_courses)
        sub = output / name
        sub.mkdir(parents=True, exist_ok=True)
        (sub / f"{name}-REAL-PARTS-EXPERIMENT.ldr").write_text(
            _ldraw(parts,w,length, f"Boldungo Mission A {name}"),encoding="utf8")
        (sub / f"{name}-EVIDENCE.json").write_text(
            json.dumps(audit,ensure_ascii=False,indent=2)+"\n", encoding="utf8")
        (sub / f"{name}-ELEVATION-TECHNIQUE.svg").write_text(
            _technical_elevation_svg(parts,w,length,name),encoding="utf8")
        (sub / f"{name}-BOM.json").write_text(
            json.dumps(audit["bom_ldraw"],indent=2)+"\n",encoding="utf8")
        (sub / f"{name}-ASSEMBLY-ORDER.md").write_text(
            "# "+name+" experimental assembly (NOT insertion validated)\n\n"+
            "\n".join(f"{i+1}. {s}" for i,s in enumerate(audit["nominal_build_order"]))+
            "\n\nSTOP: full mesh collisions, hand insertion, strength and stability are not certified.\n",encoding="utf8")
        assert sum(audit["bom_ldraw"].values()) == audit["total_parts"]
        print("MISSION_A_CASE", name, json.dumps({
            k:audit[k] for k in ("width_studs","length_studs","total_parts","roof_parts",
            "unsupported_nominal_count","connected_components_nominal",
            "orthogonal_body_aabb_collision_count","supported_roof_to_baseplate_nominal")}))
        report.append({"case":name,**audit})
    (output/"COMPARE-THREE-HOUSES.json").write_text(
        json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    print("MISSION_A_EXPERIMENTS",len(report),"N6_NOT_CERTIFIED")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--output",default="artifacts/lego2-mission-a")
    main(p.parse_args().output)
