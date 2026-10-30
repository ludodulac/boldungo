"""Assembly analysis using a conservative spatial broad phase."""

from __future__ import annotations

from collections.abc import Sequence

from .core import (
    AssemblyReport,
    CONTACT_EPS,
    PartInstance,
    Relation,
    check_collision,
    find_connections,
)
from .spatial import candidate_pairs


def _validate_instance_ids(parts: Sequence[PartInstance]) -> None:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for part in parts:
        if part.instance_id in seen:
            duplicates.add(part.instance_id)
        seen.add(part.instance_id)
    if duplicates:
        duplicate_list = ", ".join(repr(value) for value in sorted(duplicates))
        raise ValueError(f"Assembly instance_id values must be unique; duplicates: {duplicate_list}")


def analyze_assembly(parts: Sequence[PartInstance]) -> AssemblyReport:
    """Connect only *demonstrated* nominal joints; never excuse a mesh collision.

    Simple surface touching is not a stud/cavity connection. Floating and
    ambiguous pieces cannot become supported merely through contact.
    """
    from .joint_validation import assess_pair
    _validate_instance_ids(parts)
    collisions, contacts, connections, uncertain=[],[],[],[]
    graph={p.instance_id:set() for p in parts}
    for a,b in candidate_pairs(parts):
        nominal=find_connections(a,b)
        relation=check_collision(a,b)
        verdict=assess_pair(a,b,relation=relation,connections=nominal)
        item={"part_a":a.instance_id,"part_b":b.instance_id,
              "type":verdict.verdict,"reason":verdict.reason}
        if verdict.verdict=="FORBIDDEN_COLLISION":
            collisions.append(item)
        elif verdict.verdict=="INDETERMINATE":
            uncertain.append(item)
        elif verdict.verdict=="COMPATIBLE_MATING":
            contacts.append({**item,"type":"verified_nominal_mating"})
            connections.extend(nominal)
            graph[a.instance_id].add(b.instance_id)
            graph[b.instance_id].add(a.instance_id)
        elif relation is Relation.CONTACT:
            contacts.append({**item,"type":"surface_contact_without_attachment"})
    # Historical base heuristic retained, but only VERIFIED edges can reach it.
    # This is topological nominal support, not physical load-bearing certification.
    if parts:
        base=max(part.bbox.maximum[1] for part in parts)
        roots={part.instance_id for part in parts if abs(part.bbox.maximum[1]-base)<=CONTACT_EPS}
    else: roots=set()
    supported=set(roots)
    frontier=list(roots)
    while frontier:
        node=frontier.pop()
        for neighbor in graph[node]:
            if neighbor not in supported:
                supported.add(neighbor)
                frontier.append(neighbor)
    unsupported=[part.instance_id for part in parts if part.instance_id not in supported]
    components=[]
    unseen=set(graph)
    while unseen:
        start=next(iter(unseen));component=set();stack=[start]
        while stack:
            node=stack.pop()
            if node in component:continue
            component.add(node);unseen.discard(node);stack.extend(graph[node]-component)
        components.append(sorted(component))
    return AssemblyReport(not collisions and not uncertain and not unsupported,
                          collisions,contacts,connections,unsupported,
                          sorted(components),uncertain)
