import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
NEW=ROOT/'frontend/module-001-baseline57-export.json'
OLD=ROOT/'frontend/module-001-export.json'
def load(p): return json.loads(p.read_text())
def cells(p):
 w,l,h=p.get('width_studs',1),p.get('length_studs',1),p.get('height_plates',3 if p['category']=='brick' else 1)
 if p['rotation_quarter_turns']%2: w,l=l,w
 return {(p['x_studs']+dx,p['y_studs']+dy,p['z_plates']+dz) for dx in range(w) for dy in range(l) for dz in range(h)}
def test_module_001_baseline57_contract_and_history():
 n=load(NEW);o=load(OLD);assert n['metadata']['module_id']=='MODULE_001_BASELINE57';assert (n['brick_model']['width_studs'],n['brick_model']['depth_studs'],n['brick_model']['height_plates'])==(57,71,162);assert o['brick_model']['width_studs']==24 and o['brick_model']['depth_studs']==20 and o['brick_model']['height_plates']==45
def test_module_001_baseline57_bom_envelope_collision_support():
 n=load(NEW); ps=n['brick_model']['parts']; assert n['bom']['total_parts']==len(ps);assert sum(x['quantity'] for x in n['bom']['lines'])==len(ps)
 occ=set(); bytop={}
 for p in ps:
  c=cells(p);assert all(0<=x<57 and 0<=y<71 and 0<=z<162 for x,y,z in c);assert not occ.intersection(c);occ|=c
  for x,y,z in c: bytop.setdefault(z,set()).add((x,y))
 for p in ps:
  if p['z_plates']==0: continue
  footprint={(x,y) for x,y,z in cells(p) if z==p['z_plates']}
  assert footprint & bytop.get(p['z_plates']-1,set()), p['placement_id']
def test_module_001_baseline57_perimeter_and_front_rear_gables():
 n=load(NEW);ps=n['brick_model']['parts'];occ=set().union(*(cells(p) for p in ps))
 for z in range(140):
  assert all((x,0,z) in occ and (x,70,z) in occ for x in range(57));assert all((0,y,z) in occ and (56,y,z) in occ for y in range(71))
 front=[p for p in ps if p.get('facade')=='front' and p['z_plates']>=140];rear=[p for p in ps if p.get('facade')=='rear' and p['z_plates']>=140]
 assert front and rear
 sig=lambda p:(p['part_id'],p['x_studs'],p['z_plates'],p['rotation_quarter_turns'],p.get('width_studs'),p.get('length_studs'),p.get('height_plates'))
 assert sorted(map(sig,front))==sorted(map(sig,rear))
 assert max(z for x,y,z in occ)==161
