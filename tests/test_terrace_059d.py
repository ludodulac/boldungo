"""059D graph checks: UNKNOWN never establishes a supported LEGO connection."""
from scripts.assembly_terrace_059d import reachable


def test_valid_only_path():
    parts=[{"placement_id":name} for name in ("post","board","cross")]
    edges=[{"a":"post","b":"board","status":"VALID"},
           {"a":"board","b":"cross","status":"UNKNOWN"}]
    assert reachable(parts,edges,{"post"})=={"post","board"}


def test_valid_chain_reaches_all():
    parts=[{"placement_id":name} for name in ("post","board","cross")]
    edges=[{"a":"post","b":"board","status":"VALID"},
           {"a":"board","b":"cross","status":"VALID"}]
    assert reachable(parts,edges,{"post"})=={"post","board","cross"}


def test_blocked_piece_is_not_installed(monkeypatch):
    from scripts import assembly_terrace_059d as assembly
    fixed=[{"placement_id":"fixed"}]
    scope=[{"placement_id":"hidden-cross-bond:01","x_studs":0,"y_studs":0,"z_plates":0},
           {"placement_id":"rail-post:02","x_studs":1,"y_studs":0,"z_plates":0}]
    calls=[]
    def fake_check(piece,installed):
        calls.append((piece["placement_id"],[p["placement_id"] for p in installed]))
        return {"verdict":"BLOCKED","blockers":["fixed"],"unknown":[]}
    monkeypatch.setattr(assembly,"check",fake_check)
    monkeypatch.setattr(assembly,"connection",lambda a,b:{"status":"INVALID"})
    steps=assembly.ordered_finishes(scope,fixed,[])
    assert [x["verdict"] for x in steps]==["BLOCKED","NOT_TESTED"]
    assert len(calls)==1
    assert "hidden-cross-bond:01" not in steps[1]["installed"]
