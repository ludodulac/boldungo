# LEGO2-059F — plate 029:06 connection truth

## Decision: B — impossible as currently placed (rectangular solid model)

Source: GUIDED-004 1890-part brick-model.json, prior preserved export (056), inspected against current connector/catalog code at HEAD 3f02092a44ab54e62e62568250e693a58d2dcf24. Reconfirm against newest export before treating this as a fresh export-run result.

All coordinates below are canonical, in studs/plates; boxes use half-open bounds. No part or position was changed.

| Part | Type | Origin | Rotation | Bounding box (x,y,z) |
| --- | --- | --- | --- | --- |
| hidden-cross-bond-029:06 | PLATE_1X3 | (3,23,35) | 0 | [3,4) × [23,26) × [35,36) |
| board:00001 | BRICK_2X8 | (3,17,36) | 0 | [3,5) × [17,25) × [36,39) |
| board:00002 | BRICK_2X8 | (3,25,36) | 0 | [3,5) × [25,33) × [36,39) |
| hidden-cross-plate:00007-00013 | PLATE_1X6 | (3,20,35) | 1 | [3,4) × [20,26) × [35,36) |

**Contacts if considered in isolation:** plate 029:06 top at z=36 is flush with underside of board:00001 over **two stud columns** (x=3,y=23–24), and board:00002 over **one** (x=3,y=25). Those are geometrically possible stud/underside interfaces in isolation, not validated LEGO engagements. They do not support preinstallation: both boards are above the plate and are not present before docking.

**Fatal conflict in the canonical placement:** plate 029:06 and hidden-cross-plate:00007-00013 have the **same z range [35,36)** and overlap across the entire plate 029:06 footprint **[3,4) × [23,26)**. That is three studs of **positive solid-volume intersection**, not a connector plane. The cross plate is already part of the mobile anchored module. The two parts cannot occupy these same cells simultaneously as solid rectangular LEGO plates.

**Validator finding:** `backend/brickhouse/bricks/connectors.py` deliberately restricts documented connector families to BRICK_1X1, BRICK_1X8, BRICK_2X8, PLATE_1X6; PLATE_1X3 is cataloged in `catalog.py` but excluded from the documented set. For 029:06 / board:00001 or :00002, the validator returns UNKNOWN for a vertical interface because the PLATE_1X3 underside engagement has not been documented in the validator; **not** VALID. For 029:06 / cross plate, `validate_connection` returns INVALID, reason `solid-volume-collision`. This is not a missing connection rule.

**Other neighbors:** the two adjacent boards and the cross plate are the rectangular parts in the prior 1890-part export with footprint overlap and relevant z plane. A full current-export and LDraw primitive verification is still required before asserting absence of any additional nonrectangular contact. A lack of a VALID preinstallation support remains established by 059E current-scenario execution.

**Consequences:** Neither A (move 029:06 into mobile module) nor B (preinstall it as fixed) can be declared buildable at unchanged official placements, because the cross plate occupies the same solid volume. A free swept path in a limited fixed scenario cannot override this final-pose collision. Do not alter `validate_connection` to return VALID for intersecting solids.

**Required next decision:** ask Grand-père to authorize a later **physical/model placement or part-layout correction** resolving the overlap between the existing cross plate and 029:06. Do not select a replacement, alter coordinates, or mutate GUIDED-004 under mission 059F. No complete build order or 60-operation PASS is claimed. Mechanical strength remains uncertified.
