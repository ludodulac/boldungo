"""059C rigid-module sweep regression checks; no official model mutation."""
from scripts.assembly_sequence_059b import rigid_module_install
from scripts.prototype_terrace_059b import T1,T2


def test_rigid_module_detects_intermediate_obstacle():
    obstacle={**T1,"placement_id":"fixed:obstacle","z_plates":40}
    result=rigid_module_install([T1,T2],[obstacle])
    assert result["verdict"]=="BLOCKED"
    assert result["first_blocked"]["mobile"]==T1["placement_id"]
    assert result["first_blocked"]["blockers"][0]["fixed"]=="fixed:obstacle"


def test_rigid_module_empty_space_is_geometry_pass():
    result=rigid_module_install([T1,T2],[])
    assert result["verdict"]=="GEOMETRY_PASS"
    assert len(result["checks"])==2


def test_rigid_module_unknown_local_geometry():
    unknown={**T1,"placement_id":"fixed:unknown","part_id":"NOT_IN_CATALOG"}
    result=rigid_module_install([T1],[unknown])
    assert result["verdict"]=="UNKNOWN"
    assert "fixed:unknown" in result["first_unknown"]["unknown"]
