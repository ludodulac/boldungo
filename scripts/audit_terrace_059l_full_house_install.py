"""059L: whole-GUIDED-004 staged terrace B/C AABB audit; NEVER a strength certificate.

Official 1890 parts are read-only. T1/T2 are experiments, NOT official parts.
The module is assumed preassembled in hand; connector grip is not proven.
"""
import json
import sys
from pathlib import Path

try:
    from scripts.audit_terrace_048 import box, overlap
except ModuleNotFoundError:
    from audit_terrace_048 import box, overlap

P = 'scene-platform:south-timber-deck-'
J = 'guided004-031:concrete-timber-cross-joint:'
PARAPET = 'scene-platform:south-concrete-platform:y_max:parapet:00428'


def cross(name, y):
    return dict(placement_id='EXPERIMENT:059B:'+name, part_id='BRICK_1X8',
                category='brick', component='roof_support',
                x_studs=6, y_studs=y, z_plates=33,
                rotation_quarter_turns=1)


def swept(p):
    b = box(p)
    if b is None:
        return None
    return b[0],b[1],b[2],b[3],b[4],b[5]+30


def blocked(moving, fixed):
    f = [(q['placement_id'], box(q)) for q in fixed]
    return [(p['placement_id'],qid) for p in moving if (path:=swept(p))
            for qid,qb in f if qb is not None and overlap(path,qb)]


def connection(a,b):
    A,B=box(a),box(b)
    if A is None or B is None or not (A[5]==B[2] or B[5]==A[2]):
        return 0
    return max(0,min(A[3],B[3])-max(A[0],B[0]))*max(0,min(A[4],B[4])-max(A[1],B[1]))


def components(parts):
    g = {p['placement_id']:set() for p in parts}
    for i,a in enumerate(parts):
        for b in parts[i+1:]:
            if connection(a,b):
                g[a['placement_id']].add(b['placement_id'])
                g[b['placement_id']].add(a['placement_id'])
    remaining=set(g); sizes=[]; isolated=[]
    while remaining:
        root=remaining.pop(); seen={root}; pending=[root]
        while pending:
            for n in g[pending.pop()]&remaining:
                remaining.remove(n);pending.append(n);seen.add(n)
        sizes.append(len(seen))
        if len(seen)==1: isolated.append(root)
    return sorted(sizes,reverse=True),sorted(isolated)


def study(model,variant):
    assert variant in ('B','C')
    full=model['parts']; assert len(full)==1890
    ids={p['placement_id'] for p in full};assert len(ids)==1890
    by={p['placement_id']:p for p in full}
    floor=[p for p in full if p['placement_id'].startswith(P)
           and (':board:' in p['placement_id'] or ':hidden-' in p['placement_id'])]
    support=[p for p in full if p['placement_id'].startswith(P)
             and 'support-solution:timber-post' in p['placement_id']]
    rails=[p for p in full if p['placement_id'].startswith(P) and ':rail-' in p['placement_id']]
    joints=[p for p in full if 'west-return-rail:cross-joint' in p['placement_id']]
    assert (len(floor),len(support),len(rails),len(joints))==(30,36,39,3)
    module=[*floor,cross('T1',19)]
    if variant=='C': module.append(cross('T2',22))
    crossings=[by[J+n] for n in ('03','04','05','06')]
    later=[*crossings,by[PARAPET],*sorted([*rails,*joints],key=lambda p:(p['z_plates'],p['placement_id']))]
    future={p['placement_id'] for p in floor+later}
    fixed=[p for p in full if p['placement_id'] not in future]
    naive=blocked(module,[p for p in full if p['placement_id'] not in {q['placement_id'] for q in floor}])
    dock=blocked(module,fixed)
    installed=[*fixed,*module]; later_blocks=[]
    for p in later:
        errors=blocked([p],installed)
        if errors: later_blocks.extend(errors)
        installed.append(p)
    fc,isolated=components(floor)
    with_rails,_=components(floor+rails)
    prefix='scene-platform:south-timber-deck-main:'
    bridge={
        'board33_to_railpost':connection(by[prefix+'board:00033'],by[prefix+'y_max:rail-post:00109']),
        'board27_to_railpost':connection(by[prefix+'board:00027'],by[prefix+'y_max:rail-post:00109'])}
    floor_ids={x['placement_id'] for x in floor}
    hosts=[{'floor':a['placement_id'],'below':q['placement_id'],'studs':connection(a,q)}
           for a in floor for q in full if q['placement_id'] not in floor_ids
           and connection(a,q) and box(a)[2]==box(q)[5]]
    near_unknown=[p['placement_id'] for p in full if box(p) is None
                  and 0<=p['x_studs']<=14 and 14<=p['y_studs']<=45
                  and 30<=p['z_plates']<=80]
    return dict(variant=variant,original_parts=1890,experimental=[p['placement_id'] for p in module[30:]],
                naive_full_house_blockers=len(naive),staged_floor_blockers=dock,
                later_stages=len(later),later_blockers=later_blocks,
                floor_geometric_components=fc,floor_isolated=isolated,
                combined_floor_and_rail_components=with_rails,
                board33_nominal_bridge=bridge,floor_lower_host_contacts=hosts,
                nearby_unmodeled_parts=near_unknown,
                connection_strength='NOT_CERTIFIED',physical_buildability='NOT_CERTIFIED')


def main(path):
    source=Path(path);before=source.read_bytes();model=json.loads(before)
    dest=Path('artifacts/lego2-059b');dest.mkdir(parents=True,exist_ok=True)
    for v in ('B','C'):
        result=study(model,v)
        (dest/f'059l-integrated-terrace-{v}.json').write_text(json.dumps(result,indent=2))
        print(json.dumps({k:result[k] for k in ('variant','naive_full_house_blockers','staged_floor_blockers','later_stages','later_blockers','floor_geometric_components','combined_floor_and_rail_components','board33_nominal_bridge','physical_buildability')},indent=2))
        assert not result['staged_floor_blockers'] and not result['later_blockers']
    assert source.read_bytes()==before

if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit('Usage: audit_terrace_059l_compact.py brick-model.json')
    main(sys.argv[1])
