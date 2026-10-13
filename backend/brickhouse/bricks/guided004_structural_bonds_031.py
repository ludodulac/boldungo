"""031: real cross-course bond between concrete parapet and timber deck.

Exact-volume local retessellation at x=10..14, y=16..25, z=36..39.
No scene edits. A 1x2 brick spans the concrete/timber seam at x=12,
y=16..18, making a genuine single LEGO piece across both islands.
"""
from .brick_model import BrickModel, BrickModelPart
from .catalog import standard_orthogonal_definitions

CONCRETE = "scene-platform:south-concrete-platform:y_max:parapet:00427"
TIMBER = "scene-platform:south-timber-deck-main:board:00025"
PREFIX = "guided004-031:concrete-timber-cross-joint:"


def repair_guided004_concrete_timber(model: BrickModel) -> BrickModel:
    catalog = standard_orthogonal_definitions()
    by_id = {p.placement_id: p for p in model.parts}
    if CONCRETE not in by_id and TIMBER not in by_id:
        return model
    if CONCRETE not in by_id or TIMBER not in by_id:
        raise ValueError("031_PARTIAL_INTERFACE_MISSING")
    old = [by_id[CONCRETE], by_id[TIMBER]]
    def cells(p):
        d = catalog[p.part_id]
        w, l = d.footprint(p.rotation_quarter_turns)
        return {(x,y,z) for x in range(p.x_studs,p.x_studs+w)
                for y in range(p.y_studs,p.y_studs+l)
                for z in range(p.z_plates,p.z_plates+d.height_plates)}
    expected = set().union(*(cells(p) for p in old))
    # Concrete row x10..14,y16 plus timber rectangle x11..13,y17..25.
    # Exact cover: 2 + 1 + seam(2) + lane(8) + lane(3+4) = 19 studs.
    specs = (
        ("BRICK_1X2",10,16,36,1,old[0]),
        ("BRICK_1X1",13,16,36,0,old[0]),
        ("BRICK_1X2",12,16,36,0,old[1]),
        ("BRICK_1X8",11,17,36,0,old[1]),
        ("BRICK_1X3",12,18,36,0,old[1]),
        ("BRICK_1X4",12,21,36,0,old[1]),
    )
    new = []
    for i,(ref,x,y,z,rot,source) in enumerate(specs,1):
        d = catalog[ref]
        w,l = d.footprint(rot)
        new.append(BrickModelPart(
            placement_id=PREFIX+f"{i:02d}",part_id=ref,
            category=source.category,component=source.component,facade=source.facade,
            x_studs=x,y_studs=y,z_plates=z,rotation_quarter_turns=rot,
            width_studs=w,length_studs=l,height_plates=d.height_plates))
    # Hidden 1x2 plates below the deck bridge all three split board strips\n    # to the original x=11 board and the cross-seam at y=17.\n    for index, y in enumerate((17,18,21),7):\n        new.append(BrickModelPart(\n            placement_id=PREFIX+f"{index:02d}",part_id="PLATE_1X2",\n            category="plate",component=old[1].component,facade=old[1].facade,\n            x_studs=11,y_studs=y,z_plates=35,rotation_quarter_turns=1,\n            width_studs=2,length_studs=1,height_plates=1))\n    volumes = [cells(p) for p in new]
    if len(set().union(*volumes)) != sum(len(v) for v in volumes):
        raise ValueError("031_NEW_PARTS_OVERLAP")
    if set().union(*volumes) != expected:
        raise ValueError("031_EXTERIOR_VOLUME_CHANGED")
    # Genuine cross-seam part occupies a stud on each side of the seam.
    seam = cells(new[2])
    if not ({(12,16,36),(12,17,36)} <= seam):
        raise ValueError("031_NO_PHYSICAL_CROSS_SEAM")
    occupied = set()\n    for part in model.parts:\n        if part.placement_id not in (CONCRETE,TIMBER) and part.part_id in catalog:\n            occupied.update(cells(part))\n    for part in new:\n        if cells(part) & occupied:\n            raise ValueError("031_CROSS_JOINT_COLLISION:"+part.placement_id)\n    return model.model_copy(update={\n        "parts":[p for p in model.parts if p.placement_id not in (CONCRETE,TIMBER)]+new\n    })




# House/concrete direct bridge is BLOCKED at y=16,z=36 by actual window
# parts and at z=35 by the concrete deck. No opening is removed or shifted.
# The three major assemblies instead connect through the timber deck.
def repair_guided004_house_interfaces(model: BrickModel) -> BrickModel:
    catalog = standard_orthogonal_definitions()
    by_id = {p.placement_id: p for p in model.parts}
    old_id = "wall-000272"
    if old_id not in by_id:
        raise ValueError("031_HOUSE_TIMBER_WALL_MISSING")
    old = by_id[old_id]
    if (old.part_id,old.x_studs,old.y_studs,old.z_plates) != ("BRICK_1X8",16,20,33):
        raise ValueError("031_HOUSE_TIMBER_GEOMETRY_CHANGED")
    def cells(p):
        d=catalog[p.part_id]
        w,l=d.footprint(p.rotation_quarter_turns)
        return {(x,y,z) for x in range(p.x_studs,p.x_studs+w)
                for y in range(p.y_studs,p.y_studs+l)
                for z in range(p.z_plates,p.z_plates+d.height_plates)}
    specs=(
        ("PLATE_1X8",16,20,33,0),
        ("PLATE_1X8",16,20,34,0),
        ("PLATE_1X4",13,20,35,1),
        ("PLATE_1X3",16,21,35,0),
        ("PLATE_1X4",16,24,35,0),
    )
    new=[]
    for i,(ref,x,y,z,rot) in enumerate(specs,1):
        d=catalog[ref]
        w,l=d.footprint(rot)
        new.append(BrickModelPart(
            placement_id=f"guided004-031:house-timber:wall-retile:{i:02d}",
            part_id=ref,category="plate",component=old.component,
            facade=old.facade,x_studs=x,y_studs=y,z_plates=z,
            rotation_quarter_turns=rot,width_studs=w,length_studs=l,height_plates=1))
    volumes=[cells(p) for p in new]
    if len(set().union(*volumes)) != sum(map(len,volumes)):
        raise ValueError("031_HOUSE_TIMBER_SELF_COLLISION")
    if not cells(old) <= set().union(*volumes):
        raise ValueError("031_HOUSE_WALL_VOLUME_LOST")
    occupied=set()
    for p in model.parts:
        if p.placement_id != old_id and p.part_id in catalog:
            occupied.update(cells(p))
    for p in new:
        if cells(p) & occupied:
            raise ValueError("031_HOUSE_TIMBER_COLLISION:"+p.placement_id)
    return model.model_copy(update={
        "parts":[p for p in model.parts if p.placement_id != old_id]+new
    })
