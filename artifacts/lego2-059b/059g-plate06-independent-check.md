# LEGO2-059G — Independent footprint verification / STOP

## Critical correction to 059F

Re-inspected authentic retained GUIDED-004 export `lego2-guided004-056.zip/brick-model.json` (1890 parts). This is NOT a freshly regenerated export from the current HEAD. The 059F report's claimed full 3-stud solid overlap between PLATE_1X3 029:06 and rotated PLATE_1X6 is **not established** and appears to be a rotation/dimension interpretation error.

- 029:06: PLATE_1X3, x=3,y=23,z=35, rotation=0, canonical footprint [3,4) × [23,26), height [35,36).
- hidden-cross-plate:00007-00013: PLATE_1X6, x=3,y=20,z=35, rotation=1, exported width_studs=6,length_studs=1. **Canonical catalog definition** is width=1,length=6, and rotation=1 means footprint [3,9) × [20,21), height [35,36).
- Thus XY intersection is **zero**; no positive solid-volume collision between these two plates. The 059F report had incorrectly interpreted rotated width/length by treating the exported (6,1) as unrotated and then effectively rotating it again / ignoring rotation.

The BrickHouse `_box` routine obtains footprint from `standard_orthogonal_definitions().get(part_id).footprint(rotation_quarter_turns)`, which is the appropriate source for these coordinates. The exported `width_studs=6,length_studs=1` is already rotated. Never rotate that pair again.

### Consequence for the requested deletion experiment

The premise that 029:06 is fully overlapped/replaced by the PLATE_1X6 is **false on the canonical catalog footprint**. Removing 029:06 would delete an independently located plate, not remove a volume duplicate. It is therefore **not technically justified** to recommend deleting 029:06 on redundancy grounds. Whether 029:06 has another structural role is still NOT DEMONSTRATED; the existing validator excludes PLATE_1X3 from documented VALID connections. The 059E zero VALID preinstallation-support result still applies only to its restricted fixed scenario.

No official model changes, no connector rule changes, no invented reinforcement. Before any deletion decision, regenerate current GUIDED-004, compare canonical bounding boxes and connection graph, then inspect LDraw primitives and assembly order. **Decision: NON DÉMONTRÉ; ÉTUDE SUPPLÉMENTAIRE.**

This note explicitly supersedes the overlapping-volume assertion in `059f-plate06-connection-truth.md`; do not use that assertion to authorize a physical correction.
