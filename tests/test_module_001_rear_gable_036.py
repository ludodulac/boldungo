import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(): return json.loads((ROOT/'frontend/module-001-baseline57-export.json').read_text())
def dims(p):
 l=int(p['part_id'].split('X')[-1]);w=1
 if p['rotation_quarter_turns']%2:w,l=l,w
 return w,l,p.get('height_plates',3 if p['category']=='brick' else 1)
def cells(p):
 w,l,h=dims(p);return {(p['x_studs']+x,p['y_studs']+y,p['z_plates']+z) for x in range(w) for y in range(l) for z in range(h)}
def test_rear_gable_human_gate_036():
 j=load();ps=j['brick_model']['parts'];m=j['metadata'];assert m['module_id']=='MODULE_001_BASELINE57';assert m['provenance']['human_visual_gate']=='HUMAN_VISUAL_GATE_036';assert len(ps)==j['bom']['total_parts'];assert sum(x['quantity'] for x in j['bom']['lines'])==len(ps)
 assert m['rear_upper_envelope']['apex_height_plates']==162 and not m['rear_upper_envelope']['rear_chimneys_in_module_001'];assert m['rear_upper_envelope']['rear_chimneys_status']=='OPTIONAL_FUTURE_GRAFT_MODULE'
 fg=[p for p in ps if p['facade']=='front' and p['z_plates']>=140];rg=[p for p in ps if p['facade']=='rear' and p['z_plates']>=140];assert len(fg)==len(rg)>0
 sig=lambda p:(p['part_id'],p['x_studs'],p['z_plates'],p['rotation_quarter_turns'],p.get('width_studs'),p.get('length_studs'),p.get('height_plates'))
 assert sorted(map(sig,fg))==sorted(map(sig,rg));assert max(p['z_plates']+dims(p)[2] for p in fg)==162==max(p['z_plates']+dims(p)[2] for p in rg)
 occ=set();top={}
 for p in ps:
  c=cells(p);assert all(0<=x<57 and 0<=y<71 and 0<=z<162 for x,y,z in c);assert not occ&c;occ|=c
  for x,y,z in c:top.setdefault(z,set()).add((x,y))
 for p in ps:
  if p['z_plates']==0:continue
  fp={(x,y) for x,y,z in cells(p) if z==p['z_plates']};assert fp&top.get(p['z_plates']-1,set()),p['placement_id']
 assert all(p.get('component')=='wall' for p in ps);assert not any('chimney' in (str(p).lower()) for p in ps)
