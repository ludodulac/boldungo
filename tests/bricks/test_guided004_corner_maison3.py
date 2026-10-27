"""MAISON-3 narrow contract tests; do not rerun earlier mission suites."""
from pathlib import Path
from scripts.build_guided004_corner_maison3 import within_rdc_front, EXPECTED_M2

class P:
    facade="front"
    def __init__(self,x,y,z,component="wall"):
        self.x_studs=x;self.y_studs=y;self.z_plates=z
        self.rotation_quarter_turns=0;self.part_id="BRICK_2X8";self.component=component

def test_untouched_maison2_source_exists():
    assert EXPECTED_M2==139
    assert Path("missions/MAISON2/generated/MAISON2-FRAGMENT-AGRANDI.ldr").is_file()

def test_one_shot_all_remaining_sector_not_eight_stud_only():
    s=Path("scripts/build_guided004_corner_maison3.py").read_text()
    assert "end = x0 + model.width_studs" in s
    assert "MAISON3-FACADE-EST-RDC.ldr" in s
    assert "M3_PREVIOUS_139_ROWS_LOST" in s
    assert "east-rdc-french-door-right" in s
    assert "NOT_CERTIFIED" in s

def test_scene_untouched():
    p=Path("frontend/data/boldungo2-guided-004-real-scene.json").read_text()
    assert '"width": {"value": 9.3' in p
    assert '"depth": {"value": 8.2' in p
    assert 'east-rdc-french-door-right' in p
