"""M036: unmodified-B3 reproduction, genuine M031 LDCad nominal snaps,
real-mesh pair analysis. Requires pinned LDraw and external LDCad shadows
ONLY with --ldraw-root and --ldcad-shadow-root; external licenses unchanged.
No inference of mechanical stability, assembly insertion or safe collisions."""
from __future__ import annotations
import argparse
import json
import subprocess
import sys
from collections import Counter
from itertools import combinations
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
BASE=Path(__file__).resolve().parent
SOURCE=ROOT/"missions/B3/generated/GUIDED004-B3-1904.ldr"
AUDIT032=ROOT/"missions/PARALLEL-032-TOITURE/audit_032.py"
MINI=BASE/"TOITURE-036-4-PENTES-6-PIECES.ldr"
IDS=("roof-000002","roof-000003","roof-000004","roof-000005",
     "wall-000699","wall-000715")
EXPECTED_HOSTS={
"roof-000002":{"wall-000699":2,"wall-000715":1},
"roof-000003":{"wall-000715":2},
"roof-000004":{"wall-000715":2},
"roof-000005":{"wall-000715":2}
}

def named_lines(text):
    result={};label=None;count=0
    for row in text.splitlines():
        if row.startswith("0 // "):label=row[5:].strip()
        if row.startswith("1 "):
            count+=1
            if label in IDS:
                if label in result:raise AssertionError("duplicate selected ID "+label)
                result[label]=row
    return result,count

def main():
    cli=argparse.ArgumentParser()
    cli.add_argument("--ldraw-root",required=True)
    cli.add_argument("--ldcad-shadow-root",required=True)
    cli.add_argument("--out",required=True)
    a=cli.parse_args()
    source=SOURCE.read_bytes();source_text=source.decode("utf8")
    before=source
    original,nsource=named_lines(source_text)
    mini,nmini=named_lines(MINI.read_text(encoding="utf8"))
    assert nsource==1904 and len(original)==6,(nsource,original.keys())
    assert nmini==6 and list(mini)==list(IDS[4:])+list(IDS[:4])
    assert all(mini[x]==original[x] for x in IDS)
    p032=json.loads(subprocess.check_output([sys.executable,str(AUDIT032)],text=True))
    assert (p032["parts"],p032["slopes"],p032["nominal_pairs"],
            p032["roof_roof"],p032["roof_regular"])==(1904,408,832,720,112)
    sys.path.insert(0,str(ROOT/"lego_geometry_engine/src"))
    from lego_geometry_engine import (LDrawLibrary,instance_from_dict,
                                     find_connections,check_collision,Relation)
    lib=LDrawLibrary(a.ldraw_root,ldcad_shadow_root=a.ldcad_shadow_root)
    instances={}
    for iid in IDS:
        parts=original[iid].split()
        transform=[float(v) for v in parts[2:14]]
        instances[iid]=instance_from_dict({
            "instance_id":iid,"part_id":parts[14],
            "color":int(parts[1]),"transform":transform},lib)
    slope=lib.load_part("30363.dat")
    females=[s for s in slope.connectors if s.type=="anti_stud"]
    assert len(females)==8 and {s.snap_depth_ldu for s in females}=={4,8,14,20}
    assert lib.ldcad_shadow_status=="EIGHT_FEMALE_SNAP_SITES_NOMINAL_ONLY",lib.ldcad_shadow_status
    actual_nominal={i:Counter() for i in IDS[:4]}
    pair_results=[];classifications=Counter();mesh_result=Counter()
    for i,j in combinations(IDS,2):
        first,second=instances[i],instances[j]
        conn=find_connections(first,second)
        for hit in conn:
            assert hit.get("metadata_origin") and hit.get("nominal_connection_recognized") is True
            assert hit["absence_of_collision_validated"] is False
            assert hit["insertion_validated"] is False
            assert hit["stability_validated"] is False
            roof=i if i.startswith("roof-") else j if j.startswith("roof-") else None
            host=j if roof==i else i
            assert roof and host.startswith("wall-")
            actual_nominal[roof][host]+=1
        aabb=first.bbox.relation(second.bbox)
        aabb_state={"SEPARATED":"AABB_SEPARATED","CONTACT":"AABB_CONTACT",
                    "COLLISION":"AABB_OVERLAP_POTENTIAL"}[aabb.value]
        classifications[aabb_state]+=1
        relation=check_collision(first,second)
        mesh_result[relation.value]+=1
        pair_results.append({"a":i,"b":j,"ldcad_nominal":len(conn),
           "aabb":aabb_state,"mesh_engine_relation":relation.value,
           "collision_materially_forbidden_certified":False})
    assert dict(actual_nominal)=={i:Counter(v) for i,v in EXPECTED_HOSTS.items()},actual_nominal
    assert classifications==Counter({"AABB_OVERLAP_POTENTIAL":5,
                                      "AABB_CONTACT":4,"AABB_SEPARATED":6}),classifications
    assert sum(r["ldcad_nominal"] for r in pair_results)==9
    assert source==SOURCE.read_bytes(),"Original house was modified!"
    report={"mission":36,"audit032_reproduced":True,"prior_totals":p032,
       "six_original_placements_identical":True,"pinned_shadow_status":lib.ldcad_shadow_status,
       "slopes":4,"supports":2,"nominal_lcad_connections":9,
       "nominal_by_roof":{k:dict(v) for k,v in actual_nominal.items()},
       "aabb_counts":dict(classifications),"mesh_engine_counts":dict(mesh_result),
       "mesh_pairs":pair_results,"not_certified":{
          "physical_material_collision":True,"insertion":True,"stability":True,
          "complete_roof_load_path":True}}
    target=Path(a.out);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    print(json.dumps({"audit032": "PASS","ldcad_nominal":9,
             "aabb":dict(classifications),"mesh_engine":dict(mesh_result),
             "source_preserved":True},ensure_ascii=False))
if __name__=="__main__":main()
