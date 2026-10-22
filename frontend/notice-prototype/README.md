# Notice prototype — steps 1–8

Development preview for the supervised Boldüngo notice experiment.

## Open

From the repository root, serve `frontend` over HTTP (ES modules/fetch require HTTP):

```bash
cd frontend
python -m http.server 8000
```

Then open `/notice-prototype/notice-prototype.html` on that server.

## Data truth

`notice-prototype-data.json` is an **experimental derived slice**, not a constructive API. It was derived from the supplied reference run's `brick-model.json` and `assembly-plan.json`. Their SHA-256 hashes are recorded in `source`.

To verify the committed slice against the two authoritative files:

```bash
python frontend/notice-prototype/validate_notice_prototype.py /path/to/grand-pere-notice-prototype
```

The validator requires exact source hashes, exact ordered coverage of AssemblySteps 1–8, each placement exactly once, and exact BrickModel values for every displayed placement.

## Temporary pedagogical mapping

Only `step-0001` and `step-0005` are split, each into two spatial gestures. The other six AssemblySteps remain one gesture each. This local shape is deliberately private to the preview and should be replaced by the generic `AssemblyPlan -> InstructionPlan` 1..N contract when that parallel work lands.
