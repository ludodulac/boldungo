"""059M: user-authorized FOUR-part terrace strengthening preview, not official yet.

The original 1890-part GUIDED-004 export is strictly read-only.
This opt-in candidate creates a separately named, internally consistent
1894-part model, BOM, viewer and assembly plan. Nominal LDraw contact
evidence is NOT a physical strength or insertion certificate.
"""
from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path

from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.catalog import standard_orthogonal_definitions
from brickhouse.bricks.export import BrickExportBundle
from brickhouse.bricks.bom import generate_bom
from brickhouse.bricks.assembly import generate_assembly_plan
from brickhouse.bricks.instructions import generate_instruction_plan
from brickhouse.bricks.bags import generate_bag_plan
try:
    from scripts.audit_guided004_physical import audit_physical_model
    from scripts.audit_terrace_059l_full_house_install import blocked, components
except ModuleNotFoundError:  # direct CLI: python scripts/export_guided004_059m_reinforced.py
    from audit_guided004_physical import audit_physical_model
    from audit_terrace_059l_full_house_install import blocked, components

SOURCE = Path("artifacts/lego2-guided-004")
DEST = Path("artifacts/lego2-059m")
PREFIX = "scene-platform:south-timber-deck-main:"
TAG = PREFIX + "reinforcement-059m:"
SPECS = (
    ("T1", "BRICK_1X8", 6, 19, 33, 1, "timber"),
    ("T2", "BRICK_1X8", 6, 22, 33, 1, "timber"),
    ("BOARD33-Y34", "PLATE_1X3", 11, 34, 35, 1, "plate"),
    ("BOARD33-Y35", "PLATE_1X3", 11, 35, 35, 1, "plate"),
)
HOSTS = {
    PREFIX+"board:00027": ("BRICK_2X3", 11, 33, 36, 0),
    PREFIX+"board:00033": ("BRICK_1X3", 13, 33, 36, 0),
    PREFIX+"board:00007": ("BRICK_2X8", 5, 17, 36, 0),
}


def bounds(p):
    d = standard_orthogonal_definitions().get(p.part_id)
    if d is None:
        return None
    w, l = d.footprint(p.rotation_quarter_turns)
    return (p.x_studs, p.y_studs, p.z_plates,
            p.x_studs+w, p.y_studs+l, p.z_plates+d.height_plates)


def overlaps(a,b):
    return all(a[i]<b[i+3] and b[i]<a[i+3] for i in range(3))


def contact_cells(lower, upper):
    a,b=bounds(lower),bounds(upper)
    if a is None or b is None or a[5]!=b[2]:
        return []
    return [(x,y) for x in range(max(a[0],b[0]),min(a[3],b[3]))
                  for y in range(max(a[1],b[1]),min(a[4],b[4]))]


def nominal_plate_studs(plate, board):
    """Targeted nominal LDraw surfaces: 3623s01, 3002s01, 3622s01.

    BRICK_2X3: 2-wide inner wall +/-16, end wall +/-26,
    tube radius 8 at longitudinal +/-10. Stud radius 6.
    BRICK_1X3: inner wall +/-6, end wall +/-26,
    stud3 solid underside radius 4 at longitudinal +/-10.
    Cylindrical surfaces are nominal and lack tolerance/grip evidence.
    """
    assert plate.part_id=="PLATE_1X3" and plate.rotation_quarter_turns==1
    assert plate.x_studs==11 and plate.y_studs in (34,35)
    assert plate.z_plates==35 and board.z_plates==36
    assert board.rotation_quarter_turns==0 and board.y_studs==33
    cells=contact_cells(plate,board)
    assert len(cells)==(2 if board.part_id=="BRICK_2X3" else 1)
    results=[]
    for x,y in cells:
        long=-20+20*(y-board.y_studs)
        end=26-(abs(long)+6)
        if board.part_id=="BRICK_2X3":
            transverse=-10+20*(x-board.x_studs)
            side=16-(abs(transverse)+6)
            tube=min(math.hypot(transverse,long-t)-14 for t in (-10,10))
            assert side==0 and end>=0 and tube>0
            results.append({"xy":(x+.5,y+.5),"sidewall_gap":side,
                            "endwall_gap":end,"tube_gap":tube})
        else:
            assert board.part_id=="BRICK_1X3"
            assert x==board.x_studs
            side=6-6
            stud3=min(abs(long-t)-(6+4) for t in (-10,10))
            assert side==0 and end>=0 and stud3>=0
            results.append({"xy":(x+.5,y+.5),"sidewall_gap":side,
                            "endwall_gap":end,"underside_stud3_gap":stud3})
    return results


def make_preview(base: BrickModel):
    assert len(base.parts)==1890
    original=[p.model_dump(mode="json",exclude_none=True) for p in base.parts]
    by={p.placement_id:p for p in base.parts}
    assert len(by)==1890
    for key,expected in HOSTS.items():
        p=by[key]
        assert (p.part_id,p.x_studs,p.y_studs,p.z_plates,p.rotation_quarter_turns)==expected
    catalog=standard_orthogonal_definitions()
    additional=[]
    for name,ref,x,y,z,rot,category in SPECS:
        d=catalog[ref];w,l=d.footprint(rot)
        assert TAG+name not in by
        additional.append(BrickModelPart(
            placement_id=TAG+name,part_id=ref,category=category,
            component="facade_detail",facade="left",x_studs=x,
            y_studs=y,z_plates=z,rotation_quarter_turns=rot,
            width_studs=w,length_studs=l,height_plates=d.height_plates))
    all_catalog=[(p.placement_id,bounds(p)) for p in base.parts]
    all_catalog=[(pid,b) for pid,b in all_catalog if b is not None]
    for i,p in enumerate(additional):
        for pid,b in all_catalog:
            assert not overlaps(bounds(p),b),(p.placement_id,pid)
        for old in additional[:i]:
            assert not overlaps(bounds(p),bounds(old))
    edges={}
    for plate in additional[2:]:
        for boardname in ("board:00027","board:00033"):
            board=by[PREFIX+boardname]
            edges[plate.placement_id+"->"+board.placement_id]=nominal_plate_studs(plate,board)
    for beam in additional[:2]:
        contacts={name:len(contact_cells(beam,by[PREFIX+name]))
                  for name in ("board:00007","board:00013","board:00019","board:00031")}
        assert contacts=={"board:00007":1,"board:00013":2,
                          "board:00019":2,"board:00031":1}
        edges[beam.placement_id]=contacts
    preview=base.model_copy(update={"parts":[*base.parts,*additional]})
    assert len(preview.parts)==1894
    assert [p.model_dump(mode="json",exclude_none=True) for p in preview.parts[:1890]]==original
    return preview,additional,edges


def staged_audit(preview: BrickModel):
    """Collision/connection-grid proof across all modeled orthogonal house parts."""
    parts=[p.model_dump(mode="json",exclude_none=True) for p in preview.parts]
    by={p["placement_id"]:p for p in parts}
    pre="scene-platform:south-timber-deck-"
    floor=[p for p in parts if p["placement_id"].startswith(pre)
           and (":board:" in p["placement_id"] or ":hidden-" in p["placement_id"]
                or ":reinforcement-059m:" in p["placement_id"])]
    assert len(floor)==34
    after=[by["guided004-031:concrete-timber-cross-joint:"+i] for i in ("03","04","05","06")]
    after.append(by["scene-platform:south-concrete-platform:y_max:parapet:00428"])
    after.extend(sorted([p for p in parts if
                         (p["placement_id"].startswith(pre) and ":rail-" in p["placement_id"])
                         or "west-return-rail:cross-joint" in p["placement_id"]],
                        key=lambda p:(p["z_plates"],p["placement_id"])))
    assert len(after)==47
    not_fixed={p["placement_id"] for p in [*floor,*after]}
    fixed=[p for p in parts if p["placement_id"] not in not_fixed]
    assert not blocked(floor,fixed),"059M_FLOOR_INSERTION_BLOCKED"
    installed=[*fixed,*floor]
    for piece in after:
        assert not blocked([piece],installed),("059M_LATER_INSERTION_BLOCKED",piece["placement_id"])
        installed.append(piece)
    sizes,isolated=components(floor)
    assert sizes==[34] and not isolated,("059M_DISCONNECTED",sizes,isolated)
    return {"initial_house_parts":1890,"reinforced_house_parts":1894,
            "floor_module_parts":34,"floor_nominal_contact_components":sizes,
            "floor_swept_blockers":0,"later_insertion_steps":47,
            "later_swept_blockers":0,
            "all_modeled_geometry_tested":"ORTHOGONAL_AABB_ONLY",
            "real_hand_assembly":"NOT_CERTIFIED",
            "physical_clutch_strength":"NOT_CERTIFIED"}


def produce(source=SOURCE,dest=DEST):
    base=BrickModel.model_validate_json((source/"brick-model.json").read_text(encoding="utf-8"))
    source_text=(source/"brick-model.json").read_bytes()
    preview,extra,evidence=make_preview(base)
    physical=audit_physical_model(preview)
    assert physical["collision_voxel_overlaps"]==0
    staged=staged_audit(preview)
    raw_bundle=BrickExportBundle.model_validate_json((source/"viewer-export.json").read_text(encoding="utf-8"))
    plan=generate_assembly_plan(preview)
    reinforced_bundle=raw_bundle.model_copy(update={
        "brick_model":preview,
        "bom":generate_bom(preview),
        "assembly_plan":plan,
        "instruction_plan":generate_instruction_plan(plan),
        "bag_plan":generate_bag_plan(plan),
    })
    # Force the strict Pydantic consistency validation, not only model_copy.
    reinforced_bundle=BrickExportBundle.model_validate(reinforced_bundle.model_dump(mode="python"))
    assert reinforced_bundle.bom.total_parts==1894
    refs=Counter(p.part_id for p in preview.parts)
    inventory={"state":"USER_APPROVED_EXPERIMENTAL_PREVIEW_NOT_OFFICIAL",
               "original_parts":1890,"total_bricks":1894,
               "references":dict(sorted(refs.items())),
               "new_placements":[p.placement_id for p in extra],
               "nominal_ldraw_interfaces":evidence,
               "physical_audit":{"collision_voxel_overlaps":physical["collision_voxel_overlaps"]},
               "stage_geometry":staged,
               "mechanical_strength":"NOT_CERTIFIED",
               "underside_visibility":"NOT_VERIFIED_VISUALLY"}
    dest.mkdir(parents=True,exist_ok=True)
    (dest/"brick-model-reinforced.json").write_text(preview.model_dump_json(indent=2,exclude_none=True),encoding="utf-8")
    (dest/"viewer-export-reinforced.json").write_text(reinforced_bundle.model_dump_json(indent=2,exclude_none=True),encoding="utf-8")
    (dest/"inventory-reinforced.json").write_text(json.dumps(inventory,indent=2,ensure_ascii=False),encoding="utf-8")
    (dest/"assembly-constraints.json").write_text(json.dumps({
        "instruction_plan":"GENERIC_PLAN_INCLUDED_IN_VIEWER; NOT A FULLY PHYSICAL MANUAL",
        "preassemble":["059M T1/T2 under deck boards 00007/00013/00019/00031",
                       "059M two plates 1x3 beneath boards 00027 and 00033",
                       "plate 029:06 beneath board 00001 before adding board 00002"],
        "before_placing_deck":"Keep four 031 cross joints, concrete parapet 00428, and 42 rail/joint pieces uninstalled",
        "then":["Lower complete floor module onto the posts in the tested AABB corridor",
                "Fit concrete/timber cross joints 031:03–06",
                "Fit parapet 00428",
                "Fit rails and rail cross joints bottom-to-top"],
        "nominal_geometry":staged,
        "support_stud_holding":"NOT_CERTIFIED",
        "user_visible_exterior":"REQUIRES_VISUAL_REVIEW_BEFORE_OFFICIAL_PROMOTION"
    },indent=2,ensure_ascii=False),encoding="utf-8")
    assert (source/"brick-model.json").read_bytes()==source_text
    print(json.dumps({"059M":"PASS",**staged,
                      "new_parts":[p.placement_id for p in extra],
                      "viewer_bom_parts":reinforced_bundle.bom.total_parts},indent=2))
    return preview,inventory


if __name__=="__main__":
    produce()
