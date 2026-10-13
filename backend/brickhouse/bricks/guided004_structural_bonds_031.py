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
