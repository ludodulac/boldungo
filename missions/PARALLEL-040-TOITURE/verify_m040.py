"""M040: two real B3 enlargement alternatives. Fail CLOSED on geometric COLLISION.
Run only in targeted GitHub Actions with pinned LDraw and pinned external
LDCadShadowLibrary (not vendored). No global engine or B3 mutations."""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
import hashlib
import json
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
SOURCE=ROOT/"missions/B3/generated/GUIDED004-B3-1904.ldr"
M036=ROOT/"missions/PARALLEL-036-TOITURE/TOITURE-036-4-PENTES-6-PIECES.ldr"
M032=ROOT/"missions/PARALLEL-032-TOITURE/RELEVE-408.json"
OLD_ROOFS=[f"roof-{i:06d}" for i in range(2,6)]
COMMON=["wall-000699","wall-000715",*OLD_ROOFS]
OPTIONS={
 "CROSS":{
   "slopes":[*OLD_ROOFS,*[f"roof-{i:06d}" for i in range(25,29)]],
   "supports":["wall-000699","wall-000715","gable-000001"],
   "filename":"TOITURE-040-ESSAI-2-RANGEES-8-PENTES.ldr",
   "expected_snap_count":18,
   "assembly_order":["wall-000699","wall-000715","gable-000001",
       *OLD_ROOFS,*[f"roof-{i:06d}" for i in range(25,29)]],
 },
 "LONG":{
   "slopes":[f"roof-{i:06d}" for i in range(2,10)],
   "supports":["wall-000699","wall-000715","wall-000714"],
   "filename":"TOITURE-040-REPLI-BANDE-8-PENTES.ldr",
   "expected_snap_count":17,
   "assembly_order":["wall-000699","wall-000715","wall-000714",
       *[f"roof-{i:06d}" for i in range(2,10)]],
 }
}

def original_rows(text):
    rows={};current=None;count=0
    for row in text.splitlines():
        if row.startswith("0 // "):current=row[5:].strip()
        if row.startswith("1 "):
            count+=1
            if current in rows:raise AssertionError("duplicate part identifier "+current)
            rows[current]=row
    return rows,count

def original_blob(data):
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def execute(ldraw,shadow,output):
    source_bytes=SOURCE.read_bytes()
    assert original_blob(source_bytes)=="288c60fde76918128d8b955f78ebfa9afc2dfe8e"
    original,n=original_rows(source_bytes.decode("utf8"))
    assert n==1904 and len(original)==1904
    old,oldn=original_rows(M036.read_text(encoding="utf8"))
    assert oldn==6 and set(old)==set(COMMON)
    assert all(old[i]==original[i] for i in COMMON)
    m032=json.loads(M032.read_text(encoding="utf8"))
    old_p032=json.loads(subprocess.check_output(
        [sys.executable,str(ROOT/"missions/PARALLEL-032-TOITURE/audit_032.py")],text=True))
    assert (old_p032["parts"],old_p032["slopes"],
        old_p032["nominal_pairs"],old_p032["roof_roof"],
        old_p032["roof_regular"])==(1904,408,832,720,112)
    sys.path.insert(0,str(ROOT/"lego_geometry_engine/src"))
    from lego_geometry_engine import (LDrawLibrary,instance_from_dict,
        find_connections,check_collision)
    library=LDrawLibrary(ldraw,ldcad_shadow_root=shadow)
    results={}
    for option,rule in OPTIONS.items():
        rows,total=original_rows((HERE/rule["filename"]).read_text(encoding="utf8"))
        ids=[*rule["supports"],*rule["slopes"]]
        assert len(ids)==len(set(ids))==11 and total==11 and set(rows)==set(ids)
        assert all(rows[i]==original[i] for i in ids)
        assert all(rows[i]==old[i] for i in COMMON)
        instances={}
        for iid in ids:
            tokens=original[iid].split()
            instances[iid]=instance_from_dict({
              "instance_id":iid,"part_id":tokens[14],
              "color":int(tokens[1]),
              "transform":[float(x) for x in tokens[2:14]]
            },library)
        slope=library.load_part("30363.dat")
        sockets=[c for c in slope.connectors if c.type=="anti_stud"]
        assert len(sockets)==8 and set(c.snap_depth_ldu for c in sockets)=={4,8,14,20}
        assert library.ldcad_shadow_status=="EIGHT_FEMALE_SNAP_SITES_NOMINAL_ONLY"
        nominal=[];other_connections=[];contacts=Counter()
        pair_reports=[];total_new_pairs=0
        added=set(ids)-set(COMMON)
        for a,b in combinations(ids,2):
            lhs,rhs=instances[a],instances[b]
            sites=find_connections(lhs,rhs)
            for site in sites:
                pos=tuple(round(x,5) for x in site["position"])
                kind=site["type"].split(":")
                receiver=a if kind[0]=="anti_stud" else b
                host=b if receiver==a else a
                if receiver.startswith("roof-"):
                    assert site.get("nominal_connection_recognized") is True
                    assert site["absence_of_collision_validated"] is False
                    assert site["insertion_validated"] is False
                    assert site["stability_validated"] is False
                    nominal.append((receiver,host,pos,site["female_depth_ldu"]))
                elif receiver.startswith("gable-"):
                    other_connections.append({"receiver":receiver,"host":host,"world":pos,
                      "kind":site["type"]})
                else: # Other ordinary male/female sites may exist but never imply roof support
                    other_connections.append({"receiver":receiver,"host":host,"world":pos,
                      "kind":site["type"]})
            rel=check_collision(lhs,rhs)
            aabb=lhs.bbox.relation(rhs.bbox).value
            contacts[rel.value]+=1
            new_interface=bool({a,b}&added)
            total_new_pairs+=int(new_interface)
            pair_reports.append({"a":a,"b":b,"new_interface":new_interface,
                "LDCad_sites":sum(1 for s in sites if s.get("metadata_origin")),
                "other_stud_sites":sum(1 for s in sites if not s.get("metadata_origin")),
                "AABB":aabb,"mesh_engine":rel.value,
                "no_forbidden_matter_proven":False})
        # Cross-validate every female connector with the independently recorded M032 census.
        accepted=set(ids);expected=[]
        for roof in rule["slopes"]:
            row=next(e for e in m032["entries"] if e["roof_id"]==roof)
            for s in row["lower_receptions"]:
                for h in s["hits"]:
                    if h["host_id"] in accepted:
                        expected.append((roof,h["host_id"],
                            tuple(float(v) for v in s["world"]),float(s["depth_ldu"])))
        assert sorted(nominal)==sorted(expected),(option,nominal,expected)
        assert len(nominal)==rule["expected_snap_count"],(option,len(nominal))
        assert len(pair_reports)==55 and total_new_pairs==40
        results[option]={
            "sha_of_original_b3_git_blob":original_blob(source_bytes),
            "num_slopes":8,"num_supports":3,"part_count":11,
            "preserved_m036_parts":len(COMMON),
            "new_pieces":[p for p in ids if p not in COMMON],
            "nominal_ldcad":len(nominal),
            "nominal_details":[{"receiver":a,"male_host":b,"site":p,"female_depth_ldu":d}
                for a,b,p,d in sorted(nominal)],
            "other_standard_connections":other_connections,
            "mesh_engine_counts":dict(contacts),
            "mesh_collisions":[{"a":e["a"],"b":e["b"],"new":e["new_interface"]}
                for e in pair_reports if e["mesh_engine"]=="COLLISION"],
            "pairs_examined":55,"new_interface_pairs_examined":total_new_pairs,
            "pair_reports":pair_reports,
            "plausible_not_proven_order":rule["assembly_order"],
            "wall_related_parts":rule["supports"],
            "load_path_to_ground_certified":False,
            "continuous_insertion_certified":False,
            "mechanical_stability_certified":False
        }
    if SOURCE.read_bytes()!=source_bytes:raise AssertionError("original B3 changed")
    if results["CROSS"]["mesh_collisions"]:
        if not results["LONG"]["mesh_collisions"]:
            chosen="LONG"
            reason="CROSS_HAS_UNRESOLVED_ENGINE_COLLISIONS"
        else:
            chosen="M036"
            reason="BOTH_ENLARGEMENTS_HAVE_UNRESOLVED_ENGINE_COLLISIONS"
    else:
        chosen="CROSS"
        reason="NO_ENGINE_COLLISION_IN_CROSS_TRIAL_BUT_PHYSICAL_INSERTION_UNPROVEN"
    output=Path(output)
    output.parent.mkdir(parents=True,exist_ok=True)
    result={
      "mission":40,"M032_reproduction":"PASS",
      "M036_six_original_pieces":"PASS",
      "original_B3_unmodified":"PASS",
      "library_status":library.ldcad_shadow_status,
      "chosen_alternative":chosen,"selection_reason":reason,
      "results":results,
      "warning":"ENGINE CONTACT != mechanical certificate; engine COLLISION != proof of forbidden solid matter; insertion/path to ground not checked"
    }
    output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    print(json.dumps({"mission":40,"M032_reproduction":"PASS",
      "M036_preserved":"PASS",
      "CROSS":{"LDCad":results["CROSS"]["nominal_ldcad"],
        "mesh":results["CROSS"]["mesh_engine_counts"]},
      "LONG":{"LDCad":results["LONG"]["nominal_ldcad"],
        "mesh":results["LONG"]["mesh_engine_counts"]},
      "selected":chosen,"reason":reason,
      "B3_unchanged":True},ensure_ascii=False))
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--ldraw-root",required=True)
    p.add_argument("--ldcad-shadow-root",required=True)
    p.add_argument("--out",required=True)
    args=p.parse_args()
    execute(args.ldraw_root,args.ldcad_shadow_root,args.out)
