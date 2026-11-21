"""House-independent nominal LEGO clutch-interface discovery.

Find actual vertical stud-grid overlap among rectangular wall/support parts.
Reuse the existing LDraw-reviewed conservative validate_connection() rules.
A returned VALID is nominal geometry evidence, NEVER a strength certificate.
Roof slope undersides are not modeled as orthogonal connectors.
"""
from __future__ import annotations
from collections import Counter, defaultdict

from .catalog import standard_orthogonal_definitions
from .connectors import validate_connection


def audit_orthogonal_connections(model, *, max_interfaces=30000,
                                 max_examples=12):
    if min(max_interfaces, max_examples) < 1:
        raise ValueError("limits must be positive")
    catalog = standard_orthogonal_definitions()
    tops = defaultdict(list)
    bottoms = defaultdict(list)
    ignored = []
    for part in model.parts:
        if part.component not in ("wall", "roof_support") or part.category not in ("brick", "plate"):
            continue
        definition = catalog.get(part.part_id)
        if definition is None:
            ignored.append(part.placement_id)
            continue
        w, d = definition.footprint(part.rotation_quarter_turns)
        for x in range(part.x_studs, part.x_studs + w):
            for y in range(part.y_studs, part.y_studs + d):
                tops[x, y, part.z_plates + definition.height_plates].append(part)
                bottoms[x, y, part.z_plates].append(part)

    candidate_pairs = {}
    # Only matching XY stud columns and exactly matching vertical planes.
    # Adjacent masonry sidewalls must never count as LEGO clutch.
    for cell in sorted(set(tops) & set(bottoms)):
        for low in tops[cell]:
            for high in bottoms[cell]:
                if low.placement_id != high.placement_id:
                    key = (low.placement_id, high.placement_id)
                    candidate_pairs[key] = (low, high)

    checked = 0
    counts = Counter()
    examples = []
    for key in sorted(candidate_pairs)[:max_interfaces]:
        low, high = candidate_pairs[key]
        evidence = validate_connection(low, high)
        counts[evidence.status] += 1
        checked += 1
        if len(examples) < max_examples:
            examples.append({
                "lower": low.placement_id, "upper": high.placement_id,
                "status": evidence.status,
                "overlapping_stud_columns": evidence.interface_count,
                "reason": evidence.reason,
            })
    return {
        "building_id": model.building_id,
        "candidate_interfaces": len(candidate_pairs),
        "checked_interfaces": checked,
        "examination_truncated": len(candidate_pairs) > checked,
        "status_counts": dict(sorted(counts.items())),
        "examples": examples,
        "unsupported_orthogonal_ids": sorted(ignored)[:12],
        "scope": "Vertical orthogonal masonry stud/underside planes only.",
        "valid_means": "Nominal LDraw-reviewed geometry, not clutch force, insertion or strength.",
        "slope_underside_interfaces": "UNKNOWN_NOT_COVERED_BY_ORTHOGONAL_CONNECTORS",
        "physical_certification": "NOT_CERTIFIED",
    }
