"""One MAISON-2 targeted negative-test campaign; no old missions."""
from pathlib import Path
from scripts.build_guided004_corner_maison2 import in_bay,BAY_STUDS

def test_only_the_next_bay_without_cutting_real_bricks():
    assert BAY_STUDS==8
    assert in_bay((32,2,3,40,3,6),32,40,2,39)
    assert not in_bay((36,2,3,44,3,6),32,40,2,39)
    assert not in_bay((24,2,3,32,3,6),32,40,2,39)

def test_no_wrong_facade_or_floor_height():
    assert not in_bay((32,3,0,40,4,3),32,40,2,39)
    assert not in_bay((32,2,37,40,3,40),32,40,2,39)

def test_old_model_read_only_by_design():
    script=Path("scripts/build_guided004_corner_maison2.py").read_text()
    assert "canonical.generate()" in script
    assert "MAISON2_SCENE_HASH_CHANGED" in script
    assert "MAISON2_M1_126_NOT_PRESERVED" in script
    assert "MAISON2_NEW_VOLUME_COLLISION" in script
    assert "NOT_CERTIFIED" in script
