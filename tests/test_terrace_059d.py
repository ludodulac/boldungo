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
