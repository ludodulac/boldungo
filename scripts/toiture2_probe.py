"""TOITURE-2: one 3002 replacement, original roof 30363, original 3622 root.

NO correction of B-3. Negative tests and official LDraw containment + full
continuous vertical swept stud-cylinder proof. A center match is NOT a PASS.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from lego_geometry_engine import (LDrawLibrary, Relation, check_collision,
                                  find_connections, instantiate, transform_from_ldraw)
from lego_geometry_engine.joint_validation import first_mesh_crossing
from toiture1_probe import ensure_geometry_sources, stud_clearance_sloped, EPS

ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "missions" / "TOITURE2"
IDS = (
    "scene-chimney:house-chimney-antenna:00043:solution",
    "TOITURE2-VARIANT-3002",
    "roof-000338",
)
LOWER, BRIDGE, ROOF = IDS
APPROACH_LDU = 48.0


def write(name, data):
    (DIR / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_rows():
    """Strictly match the original TWO B-3 placements and 3002 proposal."""
    found = {}
    marker = None
    for line in (DIR / "MODULE-VARIANTE-3002.ldr").read_text().splitlines():
        if line.startswith("0 // "):
            marker = line[5:].split()[0]
        elif line.startswith("1 "):
            assert marker is not None and marker not in found
            found[marker] = line.split()
            marker = None
    assert list(found) == list(IDS), "Unexpected placement or order"
    assert found[LOWER] == "1 19 950 -840 630 0 0 -1 0 1 0 1 0 0 3622.dat".split()
    assert found[BRIDGE] == "1 19 960 -864 630 0 0 -1 0 1 0 1 0 0 3002.dat".split()
    assert found[ROOF] == "1 1 970 -888 620 0 0 -1 0 1 0 1 0 0 30363.dat".split()
    original = (ROOT / "missions/TOITURE1/MODULE-B3-ORIGINAL.ldr").read_text()
    assert "1 19 950 -864 630 0 0 -1 0 1 0 1 0 0 3622.dat" in original
    return found


def verify_official_details(root):
    from pathlib import Path
    roof_details = ensure_geometry_sources(root)
    geom = (root / "parts/s/3002s01.dat").read_text().lower()
    part = (root / "parts/3002.dat").read_text().lower()
    assert "s\\3002s01.dat" in part
    assert "0 ~brick  2 x  3 without front face" in geom
    assert "1 16 0 24 0 26 0 0 0 -20 0 0 0 16 box5.dat" in geom
    stud_lines = [
        "1 16 20 0 10 1 0 0 0 1 0 0 0 1 stud.dat",
        "1 16 0 0 10 1 0 0 0 1 0 0 0 1 stud.dat",
        "1 16 -20 0 10 1 0 0 0 1 0 0 0 1 stud.dat",
        "1 16 20 0 -10 1 0 0 0 1 0 0 0 1 stud.dat",
        "1 16 0 0 -10 1 0 0 0 1 0 0 0 1 stud.dat",
        "1 16 -20 0 -10 1 0 0 0 1 0 0 0 1 stud.dat",
    ]
    assert all(x in geom for x in stud_lines), "Official 3002 stud locations unexpected"
    return {**roof_details, "real_support": "3002.dat (Brick 2 x 3)",
            "support_upper_studs_local": [[x, 0, z] for x in (-20, 0, 20) for z in (-10, 10)],
            "support_lower_cavity": "actual inverted inner box5.dat; no presumed physical tolerances"}


def positions(part, typename):
    return sorted([tuple(part.transform.point(c.position))
                   for c in part.definition.connectors if c.type == typename])


def center_matches(centers,studs):
    return [list(a) for a in centers if any(math.dist(a,b)<=EPS for b in studs)]


def body_dimensions_3002(mid):
    """Nominal upright 2x3 brick, verified from actual LDraw bounding triangles."""
    box = mid.definition.bbox
    observed = [box.maximum[i]-box.minimum[i] for i in range(3)]
    # LDraw body X60 Z40, nominal body Y 0..24, stud top -4.
    return {"observed_mesh_extent_xyz_ldu": observed,
            "real_official_nominal_2x3": all(abs(v-w)<=EPS for v,w in zip(observed,(60,28,40))),
            "world_body_upper_y": mid.transform.point((0,0,0))[1],
            "world_body_lower_y": mid.transform.point((0,24,0))[1]}


def vertical_certificate(moving, stationary, *, role):
    """WHOLE continuous interval: body plane separation and all fixed studs.

    LDraw world Y grows down. At t=1 moving body lower face rests at
    stationary body upper face; at any t<1 it lies strictly above it.
    The moving actual mesh is tested analytically against the full
    vertical sweep of all fixed stud cylinders (no discrete sampling).
    """
    final_low=moving.transform.point((0,24,0))[1]
    lower_upper=stationary.transform.point((0,0,0))[1]
    body_clear=final_low<=lower_upper+EPS
    first_max=moving.bbox.maximum[1]-APPROACH_LDU
    first_min=stationary.bbox.minimum[1]
    start_clear=first_max < first_min-EPS
    sweep=stud_clearance_sloped(moving,stationary)
    threats=[s for s in sweep if not s["continuous_sweep_clear"]]
    return {
        "role":role,"final_moving_body_bottom_y":final_low,
        "stationary_body_top_y":lower_upper,"continuously_separated_solid_bodies":body_clear,
        "start_upper_mesh_max_y":first_max,"stationary_mesh_min_y":first_min,
        "start_disjoint":start_clear,
        "fixed_studs_checked":len(sweep),
        "all_studs_clear_for_entire_continuous_sweep":not threats,
        "stud_sweep_details":sweep,
        "threats":threats,
        "status":"PASS" if body_clear and start_clear and not threats else "NON DÉMONTRÉ",
    }


def main(ldraw):
    source=read_rows()
    source_details=verify_official_details(ldraw)
    library=LDrawLibrary(ldraw)
    instances={}
    for id in IDS:
        tokens=source[id]
        data=list(map(float,tokens[2:14]))
        real=library.load_part(tokens[14])
        instances[id]=instantiate(real,id,transform_from_ldraw(data),int(tokens[1]))
        assert len(real.triangles)>0
    bottom,bridge,roof=[instances[k] for k in IDS]
    # Verify 3002 geometric dimensions rather than accepting metadata alone.
    bridge_body=body_dimensions_3002(bridge)
    assert bridge_body["real_official_nominal_2x3"],bridge_body

    lower_conn=find_connections(bottom,bridge)
    lower_rel=check_collision(bottom,bridge)
    # Our specialized geometry-engine assess_pair conservatively returns
    # INDETERMINATE on uncommon parts, so this local proof requires actual
    # official 3002 coordinates, connector matches, body separation and sweep.
    lower_studs=positions(bottom,"stud")
    bridge_bottoms=positions(bridge,"anti_stud")
    lower_matches=center_matches(bridge_bottoms,lower_studs)
    assert len(lower_matches)==3,"Unexpected real 3622->3002 connector count"

    bridge_studs=positions(bridge,"stud")
    # The 30363 lower cavities near the high-end foot: candidates are taken
    # from official roof subpart's lower face at y=24, x±10 and local z0.
    # They are NOT permanent globally inferred connectors. They must pass
    # the physical mesh clearance test below, never count by themselves.
    local_roof_cavities=[(-10.0,24.0,0.0),(10.0,24.0,0.0)]
    world_roof_cavities=[tuple(roof.transform.point(x)) for x in local_roof_cavities]
    roof_matches=center_matches(world_roof_cavities,bridge_studs)

    # Test original 3622 upper WITHOUT retrying its full prior 3-piece audit:
    # its already measured connector centers are in the published TOITURE1 report.
    prev=json.loads((ROOT/"missions/TOITURE1/CONNEXIONS.json").read_text())
    assert prev["original_roof_pair_nominal_match_count"]==0
    assert len(roof_matches)==2, "Proposed 3002 did not align both high-end roof cavities"

    roof_rel=check_collision(roof,bridge)
    bridge_bottom_rel=check_collision(bridge,bottom)
    roof_bottom_rel=check_collision(roof,bottom)
    bottom_up=vertical_certificate(bridge,bottom,role="3622 existing lower to 3002 variant")
    bridge_up=vertical_certificate(roof,bridge,role="3002 variant to 30363 unchanged slope")

    # Official actual mesh relationship cannot be COLLISION. We cannot
    # turn mesh collision into legal insertion from connector centers.
    no_forbidden=all(x is not Relation.COLLISION for x in
                     (roof_rel,bridge_bottom_rel,roof_bottom_rel))
    interface_proof=(len(lower_conn)>=3 and lower_rel is Relation.CONTACT
                     and len(lower_matches)==3 and bottom_up["status"]=="PASS")
    roof_proof=(roof_rel is Relation.CONTACT
                and len(roof_matches)==2
                and bridge_up["status"]=="PASS"
                and roof_bottom_rel is Relation.SEPARATED)
    aligned_center_count={"lower_matches":len(lower_matches),"roof_matches":len(roof_matches)}
    mechanical_joint="PASS" if interface_proof and roof_proof and no_forbidden else "NON DÉMONTRÉ"
    solid_collision="PASS" if no_forbidden and not bottom_up["threats"] and not bridge_up["threats"] else "NON DÉMONTRÉ"
    support_chain="PASS" if mechanical_joint=="PASS" else "NON DÉMONTRÉ"
    insertion="PASS" if (interface_proof and roof_proof and
                          bottom_up["status"]=="PASS" and
                          bridge_up["status"]=="PASS") else "NON DÉMONTRÉ"

    # Negative controls on exactly the same official geometry; these are
    # isolated test positions, NEVER added to B-3 or the saved variant.
    bad_shift=instantiate(bridge.definition,"NEGATIVE-HORIZONTAL-SHIFT-10",
                          bridge.transform.compose(type(bridge.transform).translation(10,0,0)))
    bad_height=instantiate(bridge.definition,"NEGATIVE-HEIGHT-8",
                           bridge.transform.compose(type(bridge.transform).translation(0,8,0)))
    neg={
      "horizontal_shift_plus_10_ldu_expected_no_matched_connectors":{
          "support_matches":len(find_connections(bottom,bad_shift)),
          "roof_matches":len(center_matches(world_roof_cavities,positions(bad_shift,"stud")))},
      "vertical_shift_plus_8_ldu_expected_no_matched_connectors":{
          "support_matches":len(find_connections(bottom,bad_height)),
          "roof_matches":len(center_matches(world_roof_cavities,positions(bad_height,"stud")))},
      "identical_solid_3002_duplicate":check_collision(bridge,
          instantiate(bridge.definition,"NEGATIVE-COINCIDENT",bridge.transform)).value,
      "isolated_side_surface_does_not_prove_mating":len(find_connections(bottom,
          instantiate(bridge.definition,"NEGATIVE-REMOTE",bridge.transform.compose(
              type(bridge.transform).translation(100,0,0)))))
    }
    controls_pass=(list(neg.values())[0]=={"support_matches":0,"roof_matches":0} and
                   list(neg.values())[1]=={"support_matches":0,"roof_matches":0} and
                   neg["identical_solid_3002_duplicate"]=="COLLISION" and
                   neg["isolated_side_surface_does_not_prove_mating"]==0)
    assert controls_pass,"NEGATIVE_TEST_FAILED: "+json.dumps(neg)

    fail=[]
    if roof_rel is Relation.COLLISION:fail.append("Real 30363 mesh crosses 3002 mesh; cannot justify by connector alignment.")
    if bridge_bottom_rel is Relation.COLLISION:fail.append("Real 3002 mesh crosses 3622 lower support mesh.")
    if roof_bottom_rel is Relation.COLLISION:fail.append("Real 30363 mesh crosses the original lower 3622.")
    if bottom_up["threats"]:fail.append("3002 insertion intersects a fixed 3622 stud swept cylinder: "+str(bottom_up["threats"][0]))
    if bridge_up["threats"]:fail.append("30363 insertion intersects a fixed 3002 stud swept cylinder: "+str(bridge_up["threats"][0]))
    if not roof_matches:fail.append("Roof underside stud/cavity centers do not align.")
    if not fail and not interface_proof:fail.append("Bottom 3622 to replacement 3002 stud/cavity connection not demonstrated.")
    if not fail and not roof_proof:fail.append("Upper 3002 to original roof 30363 mesh/cavity clearance not demonstrated.")

    connections={
        "official_sources":source_details,"lower_to_bridge_stud_cavity_centers":lower_matches,
        "bridge_to_roof_30363_underside_cavity_centers":roof_matches,
        "lower_engine_connector_matches":len(lower_conn),
        "lower_to_bridge_actual_mesh_relation":lower_rel.value,
        "bridge_to_roof_actual_mesh_relation":roof_rel.value,
        "roof_to_bottom_actual_mesh_relation":roof_bottom_rel.value,
        "hypothesis_replaced_original_nonmatching_center_count":0,
        "aligned_centers_alone_are_not_certification":True,
        "actual_mesh_clearance_and_continuous_sweep_necessary":True,
        "status":mechanical_joint
    }
    collision_doc={
        "all_pairs":{f"{LOWER} <> {BRIDGE}":bridge_bottom_rel.value,
                    f"{BRIDGE} <> {ROOF}":roof_rel.value,
                    f"{LOWER} <> {ROOF}":roof_bottom_rel.value},
        "lower_to_bridge_continuous_stud_sweep":bottom_up,
        "bridge_to_roof_continuous_stud_sweep":bridge_up,
        "first_mesh_crossing_if_any":first_mesh_crossing(roof,bridge) if roof_rel is Relation.COLLISION else None,
        "status":solid_collision
    }
    insertion_doc={
        "coordinate":"LDraw, +Y down",
        "parametric_trajectory_for_each_moving_part":"xyz(t)=(final_x,final_y-48+48*t,final_z), t in [0,1]",
        "method":"Entire triangle-to-cylinder projection + exact entire path body-plane separation, not sampling",
        "steps":[
            {"piece":LOWER,"role":"local foundation/root only","start":[950,-888,630],"end":[950,-840,630],
             "status":"PASS" ,"absolute_house_foundation":"NON DÉMONTRÉ"},
            {"piece":BRIDGE,"start":[960,-912,630],"end":[960,-864,630],
             "pair_with_existing_lower":bottom_up,"status":bottom_up["status"]},
            {"piece":ROOF,"start":[970,-936,620],"end":[970,-888,620],
             "pair_with_existing_bridge":bridge_up,
             "pair_with_existing_lower":roof_bottom_rel.value,
             "status":"PASS" if roof_proof else "NON DÉMONTRÉ"}],
        "status":insertion
    }
    verdict={
        "original_toiture1_upper_3622_to_roof":"NON DÉMONTRÉ (0 aligned centers, unchanged B-3)",
        "candidate_support":"3002.dat Brick 2 x 3 at x960 y-864 z630, original B-3 upper 3622 substituted in separate experimental model",
        "roof":"roof-000338 30363.dat at x970 y-888 z620, source unchanged",
        "lower_root":"scene-chimney:house-chimney-antenna:00043:solution 3622.dat unchanged",
        "variant_necessary":"OUI",
        "additional_ref":"3002.dat","new_physical_piece_count":1,
        "replaced_original_in_variant_only":"3622.dat","net_piece_count_change":0,
        "connection":mechanical_joint,"collisions":solid_collision,
        "support_to_local_lower_3622":support_chain,
        "support_to_house_foundations":"NON DÉMONTRÉ",
        "insertion":insertion,
        "visualization":"NON DÉMONTRÉ jusqu'au contrôle Chromium",
        "negative_tests":"PASS" if controls_pass else "FAIL",
        "negative_test_data":neg,
        "first_blocker":fail[0] if fail else None,
        "whole_408_piece_roof":"NOT_TESTED",
        "real_stability_and_clutch_force":"NON DÉMONTRÉ",
        "overall":"PASS" if mechanical_joint==solid_collision==support_chain==insertion=="PASS" else "NON DÉMONTRÉ",
        "scope":"ONLY exact three selected official LDraw meshes in local isolated support; no global neighboring house collision proof"
    }
    write("CONNEXIONS.json",connections)
    write("COLLISIONS.json",collision_doc)
    write("INSERTION.json",insertion_doc)
    write("RESULTAT.json",verdict)
    print("TOITURE2_MEASURED="+json.dumps({k:verdict[k] for k in
        ("connection","collisions","support_to_local_lower_3622","insertion","negative_tests","first_blocker","overall")},ensure_ascii=False),flush=True)


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--ldraw-root",type=Path,required=True)
    args=p.parse_args()
    main(args.ldraw_root)
