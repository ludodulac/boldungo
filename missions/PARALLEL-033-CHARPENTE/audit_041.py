#!/usr/bin/env python3
"""M041 isolated LDraw mesh and staged-insertion audit; no shared engine edits.

Uses real triangle/quad faces of LDraw DAT parts and primitives from a pinned
public pybricks LDraw mirror. Edge-only and coplanar contacts are separately
treated as inconclusive; no load/strength or full collision certificate.
"""
import hashlib
import json
import math
import os
import sys
import urllib.error
import urllib.request
from collections import Counter
from functools import lru_cache
from pathlib import Path

HERE = Path(__file__).resolve().parent
B3 = HERE.parent / "B3/generated/GUIDED004-B3-1904.ldr"
MODEL = HERE / "M041-GUIDED004-APPUI-ORDONNE.ldr"
PIN = "c43ed06a128a10ed65675166bf42eb6fd608b9b0"
BASE = "https://raw.githubusercontent.com/pybricks/ldraw/" + PIN + "/"
EXPECT_SHA = "288c60fde76918128d8b955f78ebfa9afc2dfe8e"
I = (1.,0.,0.,0.,1.,0.,0.,0.,1.)
OUT = HERE / "run-041"
SRC_HASHES = {}

def matrix_apply(m, p):
    return tuple(sum(m[3*i+j]*p[j] for j in range(3)) for i in range(3))

def transform(p, origin, m):
    q=matrix_apply(m,p)
    return tuple(q[i]+origin[i] for i in range(3))

def mmul(a,b):
    return tuple(sum(a[3*i+k]*b[3*k+j] for k in range(3))
                 for i in range(3) for j in range(3))

def parse_parts(path):
    parts=[]; label=None
    for line in path.read_text(encoding="utf8").splitlines():
        if line.startswith("0 // "):
            label=line[5:]
        elif line.startswith("1 "):
            v=line.split()
            assert len(v)==15, ("record",path,v)
            parts.append({"id":label or ("anonymous-"+str(len(parts))),
                          "ref":v[14].lower(),
                          "o":tuple(map(float,v[2:5])),
                          "m":tuple(map(float,v[5:14]))})
    return parts

def git_blob(data):
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

@lru_cache(maxsize=None)
def read_dat(path):
    url=BASE+path
    last_error=None
    for retry in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(
                    url,headers={"User-Agent":"BOLDUNGO-M041-audit"}),timeout=15) as req:
                data=req.read()
            text=data.decode("utf8")
            assert text.startswith("0 "), ("invalid_dat",path)
            SRC_HASHES[path]=hashlib.sha256(data).hexdigest()
            return text
        except (urllib.error.URLError,TimeoutError) as ex:
            last_error=ex
    raise RuntimeError("LDraw unavailable "+url+" : "+str(last_error))

@lru_cache(maxsize=None)
def resolve_ref(name):
    name=name.replace("\\","/").lower()
    candidates=(["parts/"+name] if name.startswith("s/") else
                ["p/"+name,"parts/"+name])
    for cand in candidates:
        try:
            return cand,read_dat(cand)
        except RuntimeError as e:
            if "404" not in str(e):
                raise
    raise RuntimeError("UNRESOLVED_LDRAW_REF "+name)

@lru_cache(maxsize=None)
def local_mesh(name):
    key,data=resolve_ref(name)
    tris=[]
    for line in data.splitlines():
        v=line.split()
        if not v: continue
        if v[0]=="1":
            assert len(v)==15,(key,line)
            o=tuple(map(float,v[2:5]));m=tuple(map(float,v[5:14]))
            for tri in local_mesh(v[14]):
                tris.append(tuple(transform(p,o,m) for p in tri))
        elif v[0] in ("3","4"):
            n=int(v[0])
            assert len(v)==2+3*n,(key,line)
            pts=[tuple(map(float,v[2+3*i:5+3*i])) for i in range(n)]
            tris.append(tuple(pts[:3]))
            if n==4: tris.append((pts[0],pts[2],pts[3]))
    if not tris:
        # LDraw edge primitives (e.g. 4-4edge.dat) intentionally consist
        # only of type-2 lines. They are not material triangle faces.
        if any(line.lstrip().startswith(("2 ","5 ")) for line in data.splitlines()):
            return tuple()
        raise ValueError("NO_REAL_FACES "+name)
    return tuple(tris)

@lru_cache(maxsize=None)
def world_mesh(ref,origin,m):
    return tuple(tuple(transform(p,origin,m) for p in tri)
                 for tri in local_mesh(ref))

def bb(pts):
    return tuple((min(p[i] for p in pts),max(p[i] for p in pts))
                 for i in range(3))

def mesh_bb(tris):
    return bb([p for tri in tris for p in tri])

def boxes_might_overlap(a,b,eps=1e-6):
    return all(a[i][1]>=b[i][0]-eps and b[i][1]>=a[i][0]-eps
               for i in range(3))

def vsub(a,b):return tuple(a[i]-b[i] for i in range(3))
def dot(a,b):return sum(a[i]*b[i] for i in range(3))
def cross(a,b):
    return (a[1]*b[2]-a[2]*b[1],
            a[2]*b[0]-a[0]*b[2],
            a[0]*b[1]-a[1]*b[0])

def edge_through_face(a,b,t,eps=1e-7):
    # Strict Möller–Trumbore: don't mistake contact at a triangle boundary
    # or a coplanar face for a proof of volumetric material penetration.
    v0,v1,v2=t
    d=vsub(b,a);e1=vsub(v1,v0);e2=vsub(v2,v0)
    h=cross(d,e2);det=dot(e1,h)
    if abs(det)<eps:return False
    inv=1./det;s=vsub(a,v0);u=dot(s,h)*inv
    if u<=eps or u>=1-eps:return False
    q=cross(s,e1);v=dot(d,q)*inv
    if v<=eps or u+v>=1-eps:return False
    hit=dot(e2,q)*inv
    return eps<hit<1-eps

def triangle_crossing(a,b):
    aa=bb(a);bbx=bb(b)
    if not boxes_might_overlap(aa,bbx):return False
    for tri,other in ((a,b),(b,a)):
        for j in range(3):
            if edge_through_face(tri[j],tri[(j+1)%3],other):
                return True
    return False

def crossings(A,B,cap=10000):
    abb=mesh_bb(A);bbb=mesh_bb(B)
    if not boxes_might_overlap(abb,bbb):
        return {"crossings":0,"considered":0,"whole_mesh_aabb_overlap":False}
    ab=[bb(t) for t in A];bbx=[bb(t) for t in B]
    hits=0;pair_count=0
    for i,t in enumerate(A):
        for j,u in enumerate(B):
            if not boxes_might_overlap(ab[i],bbx[j]):continue
            pair_count+=1
            if triangle_crossing(t,u):
                hits+=1
                if hits>=cap:break
        if hits>=cap:break
    return {"crossings":hits,"considered":pair_count,
            "whole_mesh_aabb_overlap":True,
            "max_hits_reached":hits>=cap}

def serial_part(p):
    return {"id":p["id"],"reference":p["ref"],
            "xyz":list(p["o"]),"orientation":list(p["m"])}

def main():
    raw=B3.read_bytes()
    assert git_blob(raw)==EXPECT_SHA, "ORIGINAL_B3_CHANGED"
    parts=parse_parts(B3)
    assert len(parts)==1904
    assert sum(p["ref"]=="30363.dat" for p in parts)==408
    indexed={p["id"]:p for p in parts}
    checks={
        "wall-000699":("3008.dat",(400.,-744.,50.)),
        "wall-000704":("3008.dat",(1200.,-744.,50.)),
        "gable-000001":("3008.dat",(480.,-768.,50.)),
        "gable-000005":("3008.dat",(1120.,-768.,50.)),
        "gable-000006":("3004.dat",(480.,-792.,50.)),
        "roof-000025":("30363.dat",(410.,-792.,60.)),
        "roof-000048":("30363.dat",(470.,-816.,60.))}
    for name,(ref,xyz) in checks.items():
        assert indexed[name]["ref"]==ref and indexed[name]["o"]==xyz, name
    preview=parse_parts(MODEL)
    assert len(preview)==6 and sum(p["id"].startswith("NEW ") for p in preview)==1
    existing=[p for p in preview if p["id"].startswith("existing ")]
    for p in existing:
        prior=indexed[p["id"].removeprefix("existing ")]
        assert (p["ref"],p["o"],p["m"])==(prior["ref"],prior["o"],prior["m"])
    support=next(p for p in preview if p["id"].startswith("NEW "))
    assert support["ref"]=="3004.dat" and support["o"]==(440.,-792.,50.) and support["m"]==I
    getmesh=lambda p:world_mesh(p["ref"],p["o"],p["m"])
    newmesh=getmesh(support)
    by_approx=[p for p in parts if
      abs(p["o"][0]-440)<=190 and abs(p["o"][1]+792)<=150 and
      abs(p["o"][2]-50)<=105]
    assert len(by_approx)>=20
    # Broadphase is an intentionally conservative window by origin. The
    # longest parts used within this B3 footprint are bricks 1x10 (200 LDU)
    # and slopes (80 LDU); neighbors beyond the window cannot overlap.
    original_meshes={p["id"]:getmesh(p) for p in by_approx}
    near={key:mesh for key,mesh in original_meshes.items()
          if boxes_might_overlap(mesh_bb(newmesh),mesh_bb(mesh))}
    contact={key:crossings(newmesh,m) for key,m in near.items()}
    assert "gable-000001" in near and "roof-000048" in near
    # Presence of triangle surface crossings is a conservative red flag;
    # zero edge crossings is NOT a proof of zero material overlap.
    data={
        "mission":41,
        "origin":"GUIDED004_B3_IMMUTABLE_1904",
        "source_blob_sha1":git_blob(raw),
        "source_assembly_pieces":len(parts),
        "assessed_piece_ids":sorted(by_approx_id["id"] for by_approx_id in by_approx),
        "support":serial_part(support),
        "nominal_m037":{"wall_to_gable_studs":4,"gable_to_support_studs":2,
                         "support_to_30363_sockets":2,
                         "support_socket_depths_ldu":[8,14],
                         "provenance":"M031 LDCad connector sites; not a force rating"},
        "geometry_provenance":{"mirror":"pybricks/ldraw",
           "repository_commit":PIN,"files_sha256":SRC_HASHES},
        "mesh_face_counts":{"3004":len(local_mesh("3004.dat")),
             "3008":len(local_mesh("3008.dat")),
             "30363":len(local_mesh("30363.dat"))},
        "candidate_neighbor_meshes":sorted(near),
        "static_surface_crossings":contact,
        "method_limits":"Actual LDraw triangulated DAT surface faces, strict non-coplanar edge-to-face tests. Coplanar face contact, physical stud clutch, enclosed volumes, CAD watertightness and deformation are not certified."}
    # Staged insertion: retaining the gables, but roofs have not been added.
    without_roof={k:v for k,v in original_meshes.items()
                  if not k.startswith("roof-") and k not in (support["id"],)}
    with_roof={k:v for k,v in original_meshes.items()
               if k not in (support["id"],)}
    stage={}
    for group_name,group in (("wall_gable_then_support_no_roof",without_roof),
                            ("support_with_preexisting_roof",with_roof)):
        positions=[]
        for dy in (-48,-40,-32,-24,-16,-8,0):
            p={**support,"o":(440.,-792.+dy,50.)}
            mesh=getmesh(p)
            tested={key:crossings(mesh,other,cap=150)
               for key,other in group.items()
               if boxes_might_overlap(mesh_bb(mesh),mesh_bb(other))}
            hits={k:v["crossings"] for k,v in tested.items() if v["crossings"]}
            positions.append({"shift_y_ldu":dy,"crossing_candidates":hits,
                              "mesh_aabb_contacts":sorted(tested)})
        stage[group_name]=positions
    # Roof placement after already placing the support; postpone neighboring
    # slopes to avoid claiming that the entire B3 roof has a proven sequence.
    roof=indexed["roof-000048"]
    obstacles={k:v for k,v in without_roof.items()}
    obstacles["M041-new-3004"]=newmesh
    roof_path=[]
    for dy in (-48,-40,-32,-24,-16,-8,0):
        newroof={**roof,"o":(roof["o"][0],roof["o"][1]+dy,roof["o"][2])}
        mesh=getmesh(newroof)
        touched={key:crossings(mesh,other,cap=150)
             for key,other in obstacles.items()
             if boxes_might_overlap(mesh_bb(mesh),mesh_bb(other))}
        roof_path.append({"shift_y_ldu":dy,"crossing_candidates":
                {k:v["crossings"] for k,v in touched.items() if v["crossings"]},
               "mesh_aabb_contacts":sorted(touched)})
    stage["roof_048_after_wall_gable_support_no_other_roof"]=roof_path
    data["staged_vertical_paths_8_ldu_samples"]=stage
    data["staged_path_certified"]=False
    data["full_physical_collision_free_certified"]=False
    data["mechanical_stability_certified"]=False
    data["final_verdict"]="NON_CERTIFIE"
    data["original_parts_changed"]=False
    data["next_gate"]="Continuous swept mesh and full surrounding roof insertion; structural load path and 22deg slope verified separately"
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"RESULTATS-041.json").write_text(
        json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print("M041 MESH AUDIT:",len(newmesh),"support triangles;",
          len(by_approx),"local original parts;",len(near),"neighbor AABB candidates")
    print("M041 FINAL CROSSING CANDIDATES:",{k:v["crossings"] for k,v in contact.items()})
    print("M041 STAGED PATH SAMPLES:",{k:len(v) for k,v in stage.items()})
    for path_name,samples in stage.items():
        print("M041 PATH",path_name,
              [(p["shift_y_ldu"],p["crossing_candidates"]) for p in samples])
    print("M041 LDraw true mesh DAT files:",len(SRC_HASHES))
    print("M041 ORIGINAL B3 SOURCE UNCHANGED; STRENGTH / FULL INSERTION NON-CERTIFIED")

if __name__=="__main__":
    main()
