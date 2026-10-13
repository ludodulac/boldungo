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


# House interface strategy 2: replace the top course of two wall bricks
# with standard 1-plate layers, and span the 2-stud gap using a real 1x4
# plate. Each plate bridges to a genuine adjacent platform/deck stud at z36.
# The existing wall remains solid in its x=16 column at every z.
_WALL_INTERFACES = (
    ("wall-000273", 12, 16, "house-concrete"),
    ("wall-000272", 20, 20, "house-timber"),
)


def repair_guided004_house_interfaces(model: BrickModel) -> BrickModel:
    catalog = standard_orthogonal_definitions()
    by_id = {p.placement_id: p for p in model.parts}
    if not all(pid in by_id for pid, _, _, _ in _WALL_INTERFACES):
        raise ValueError("031_HOUSE_WALL_ANCHORS_MISSING")
    def voxels(p):
        d = catalog[p.part_id]
        w, l = d.footprint(p.rotation_quarter_turns)
        return {(x,y,z) for x in range(p.x_studs,p.x_studs+w)
                for y in range(p.y_studs,p.y_studs+l)
                for z in range(p.z_plates,p.z_plates+d.height_plates)}
    removed = set()
    added = []
    for old_id, y_start, bridge_y, label in _WALL_INTERFACES:
        old = by_id[old_id]
        if (old.part_id, old.x_studs, old.y_studs, old.z_plates,
            old.rotation_quarter_turns) != ("BRICK_1X8", 16, y_start, 33, 0):
            raise ValueError("031_WALL_GEOMETRY_CHANGED:"+label)
        specs = [
            ("PLATE_1X8",16,y_start,33,0),
            ("PLATE_1X8",16,y_start,34,0),
            ("PLATE_1X4",13,bridge_y,35,1),
        ]
        # The bridge takes exactly one wall stud at y=bridge_y; preserve
        # the remaining 7 wall studs in the upper course with 1x3 + 1x4.
        if bridge_y == y_start:
            specs += [("PLATE_1X3",16,y_start+1,35,0),
                      ("PLATE_1X4",16,y_start+4,35,0)]
        else:
            specs += [("PLATE_1X4",16,y_start,35,0),
                      ("PLATE_1X3",16,y_start+5,35,0)]
        group=[]
        for i,(ref,x,y,z,rot) in enumerate(specs,1):
            d=catalog[ref]
            w,l=d.footprint(rot)
            group.append(BrickModelPart(
                placement_id=f"guided004-031:{label}:wall-retile:{i:02d}",
                part_id=ref,category="plate",component=old.component,facade=old.facade,
                x_studs=x,y_studs=y,z_plates=z,rotation_quarter_turns=rot,
                width_studs=w,length_studs=l,height_plates=1))
        old_volume=voxels(old)
        new_volumes=[voxels(p) for p in group]
        if len(set().union(*new_volumes)) != sum(map(len,new_volumes)):
            raise ValueError("031_HOUSE_BRIDGE_SELF_COLLISION:"+label)
        retained = set().union(*new_volumes) & old_volume
        if retained != old_volume:
            raise ValueError("031_WALL_EXTERIOR_REMOVED:"+label)
        added.extend(group)
        removed.add(old_id)
    occupied=set()
    for p in model.parts:
        if p.placement_id not in removed and p.part_id in catalog:
            occupied.update(voxels(p))
    for p in added:
        if voxels(p) & occupied:
            raise ValueError("031_HOUSE_BRIDGE_COLLISION:"+p.placement_id)
    return model.model_copy(update={
        "parts":[p for p in model.parts if p.placement_id not in removed]+added
    })
