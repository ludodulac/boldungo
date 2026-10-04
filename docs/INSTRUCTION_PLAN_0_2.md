# InstructionPlan 0.2 — human gesture contract

`AssemblyStep` remains the construction ordering unit. `InstructionStep` is now one human gesture explaining an ordered part of exactly one source `AssemblyStep`.

## Minimal semantic delta

- `source_assembly_step_id` identifies the single construction step being explained. Multiple sources are deliberately not supported yet.
- `added_placement_ids` replaces the serialized `placement_ids` name to make the gesture delta explicit. In-memory `InstructionStep.placement_ids` remains as a compatibility accessor.
- `boundary_reason` is either `direct_projection` or `pedagogical_split`.
- `step_id`, `sequence`, `phase`, `instruction_kind`, `focus`, and `view` remain present. A direct projection preserves the source `step_id`; split gestures receive deterministic child IDs.
- before/after states are derived from the ordered deltas and are not serialized.

## Generation and migration

`generate_instruction_plan(assembly_plan)` remains valid and defaults to direct 1:1 projection for compatibility. The authoritative export path now calls `generate_instruction_plan(assembly_plan, brick_model)` so unknown or missing BrickModel placements are rejected.

A replaceable `InstructionSplitPolicy` may partition one source step. Every policy output is checked to preserve the exact ordered `AssemblyStep.placement_ids`; it cannot reorder, add, or omit placements.

`BoundedInstructionSplitPolicy` is intentionally only a temporary deterministic guardrail demonstrating 1→N. Its placement bound is not a model of human cognition and is not the definition of a pedagogical unit.

Schema 0.1 JSON used `placement_ids` and had no source/boundary fields. Schema 0.2 accepts `placement_ids` as an input alias for the delta list, but serialized 0.2 emits `added_placement_ids`; persisted 0.1 documents therefore require source/boundary enrichment before they can be treated as verified 0.2 plans.

No insertion path, support fact, camera matrix, inventory snapshot, before/after snapshot, arrow, occlusion metric, or cognitive score is introduced by this contract.
