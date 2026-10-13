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
    volumes = [cells(p) for p in new]
    if len(set().union(*volumes)) != sum(len(v) for v in volumes):
        raise ValueError("031_NEW_PARTS_OVERLAP")
    if set().union(*volumes) != expected:
        raise ValueError("031_EXTERIOR_VOLUME_CHANGED")
    # Genuine cross-seam part occupies a stud on each side of the seam.
    seam = cells(new[2])
    if not ({(12,16,36),(12,17,36)} <= seam):
        raise ValueError("031_NO_PHYSICAL_CROSS_SEAM")
    return model.model_copy(update={
        "parts":[p for p in model.parts if p.placement_id not in (CONCRETE,TIMBER)]+new
    })



# 031 second strategy: the concrete deck already occupies x12..14,y16,z33..36.
# Crossing at z35 would collide. Instead split the concrete parapet x13,y16
# at z36 into three plate layers, with the lowest plate spanning to the wall.
# The wall x16,y16,z33..36 remains untouched and supports the bridge below.
# At the timber interface, a concealed z35 bridge replaces the upper wall
# course and engages the deck at z36.
def repair_guided004_house_interfaces(model: BrickModel) -> BrickModel:
    catalog = standard_orthogonal_definitions()
    by_id = {p.placement_id: p for p in model.parts}
    concrete_id = PREFIX + "02"
    wall_id = "wall-000272"
    if concrete_id not in by_id or wall_id not in by_id:
        raise ValueError("031_HOUSE_INTERFACE_ANCHORS_MISSING")
    concrete, wall = by_id[concrete_id], by_id[wall_id]
    if (concrete.part_id,concrete.x_studs,concrete.y_studs,concrete.z_plates) != ("BRICK_1X1",13,16,36):
        raise ValueError("031_CONCRETE_INTERFACE_GEOMETRY_CHANGED")
    if (wall.part_id,wall.x_studs,wall.y_studs,wall.z_plates) != ("BRICK_1X8",16,20,33):
        raise ValueError("031_TIMBER_INTERFACE_GEOMETRY_CHANGED")
    def cells(p):
        d=catalog[p.part_id]
        w,l=d.footprint(p.rotation_quarter_turns)
        return {(x,y,z) for x in range(p.x_studs,p.x_studs+w)
                for y in range(p.y_studs,p.y_studs+l)
                for z in range(p.z_plates,p.z_plates+d.height_plates)}
    specs=(
        ("house-concrete",concrete,(
            ("PLATE_1X4",13,16,36,1),
            ("PLATE_1X1",13,16,37,0),
            ("PLATE_1X1",13,16,38,0),
        )),
        ("house-timber",wall,(
            ("PLATE_1X8",16,20,33,0),
            ("PLATE_1X8",16,20,34,0),
            ("PLATE_1X4",13,20,35,1),
            ("PLATE_1X3",16,21,35,0),
            ("PLATE_1X4",16,24,35,0),
        )),
    )
    added=[]
    for label,source,placements in specs:
        group=[]
        for i,(ref,x,y,z,rot) in enumerate(placements,1):
            d=catalog[ref]
            w,l=d.footprint(rot)
            group.append(BrickModelPart(
                placement_id=f"guided004-031:{label}:wall-retile:{i:02d}",
                part_id=ref,category="plate",component=source.component,
                facade=source.facade,x_studs=x,y_studs=y,z_plates=z,
                rotation_quarter_turns=rot,width_studs=w,length_studs=l,height_plates=1))
        volumes=[cells(p) for p in group]
        if len(set().union(*volumes)) != sum(map(len,volumes)):
            raise ValueError("031_NEW_BRIDGE_SELF_COLLISION:"+label)
        if not cells(source) <= set().union(*volumes):
            raise ValueError("031_ORIGINAL_SURFACE_LOST:"+label)
        added.extend(group)
    removed={concrete_id,wall_id}
    occupied=set()
    for p in model.parts:
        if p.placement_id not in removed and p.part_id in catalog:
            occupied.update(cells(p))
    for p in added:
        if cells(p) & occupied:
            raise ValueError("031_BRIDGE_COLLISION:"+p.placement_id)
    return model.model_copy(update={
        "parts":[p for p in model.parts if p.placement_id not in removed]+added
    })
