import json,sys,hashlib,pathlib
root=pathlib.Path(__file__).parent; src=pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else root
preview=json.load(open(root/'notice-prototype-data.json')); brick=src/'brick-model.json'; assembly=src/'assembly-plan.json'
assert brick.exists() and assembly.exists(), 'pass path containing authoritative brick-model.json and assembly-plan.json'
assert hashlib.sha256(brick.read_bytes()).hexdigest()==preview['source']['brick_model_sha256']
assert hashlib.sha256(assembly.read_bytes()).hexdigest()==preview['source']['assembly_plan_sha256']
b=json.load(open(brick)); a=json.load(open(assembly)); authoritative=[x for s in a['steps'][:8] for x in s['placement_ids']]; shown=[x for s in preview['instruction_steps'] for x in s['placement_ids']]
assert len(authoritative)==22 and len(shown)==22
assert shown==authoritative, 'preview must preserve placement order and exact coverage'
assert len(shown)==len(set(shown)), 'each placement must appear exactly once'
assert not(set(shown)-set(authoritative))
byid={p['placement_id']:p for p in b['parts']}; assert preview['parts']==[byid[x] for x in authoritative], 'preview geometry differs from BrickModel'
assert set(shown)==set(x for s in a['steps'][:8] for x in s['placement_ids'])
assert set(shown)==set(x['placement_id'] for x in preview['parts'])
print('PASS: 8 AssemblySteps -> 10 InstructionSteps; 22/22 placements exactly once; geometry byte-values match BrickModel subset; final state == AssemblyPlan after step-0008')
