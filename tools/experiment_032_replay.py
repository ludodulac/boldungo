from pathlib import Path
from brickhouse.vision.multiview import MultiViewWorkspace, detect_continuity_uncertainties, InquiryState
p=Path("real-house-5-workspace-v3-after-inquiry-031.json")
w=MultiViewWorkspace.model_validate_json(p.read_text())
obs=w.pass_1.observations+w.pass_2.observations
hyps=w.pass_1.hypotheses+w.pass_2.hypotheses
old=detect_continuity_uncertainties(obs)
new=detect_continuity_uncertainties(obs,inquiries=w.inquiries,hypotheses=hyps)
print("OLD",[(x.id,x.subject_ref,x.property_name) for x in old])
print("NEW",[(x.id,x.subject_ref,x.property_name) for x in new])
print("RESOLVED",sum(i.state is InquiryState.RESOLVED for i in w.inquiries))
print("IRREDUCIBLE",sum(i.state is InquiryState.IRREDUCIBLE_UNKNOWN for i in w.inquiries))
