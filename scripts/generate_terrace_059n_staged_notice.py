"""059N: honest, staged terrace notice for approved 1894-part preview.

The existing 1890-part canonical GUIDED-004 remains untouched. The new
instruction/viewer artifact has exactly 1894 placements, ordered to construct
a hand-held 34-part floor before 47 geometry-tested later placements.
AABB clearance does NOT prove LEGO grip, manual handling, or strength.
"""
import json
from pathlib import Path
from brickhouse.bricks.assembly import AssemblyPlan, AssemblyStep
from brickhouse.bricks.instructions import generate_instruction_plan
from brickhouse.bricks.bags import generate_bag_plan
from brickhouse.bricks.export import BrickExportBundle

ORIGINAL=Path("artifacts/lego2-guided-004")
PREVIEW=Path("artifacts/lego2-059m")
OUTPUT=Path("artifacts/lego2-059n")
PREFIX="scene-platform:south-timber-deck-"
JOINT="guided004-031:concrete-timber-cross-joint:"
PARAPET="scene-platform:south-concrete-platform:y_max:parapet:00428"

def ordering(model):
    parts=model.parts
    by={p.placement_id:p for p in parts}
    assert len(parts)==len(by)==1894
    mobile=[p for p in parts if p.placement_id.startswith(PREFIX) and
            (":board:" in p.placement_id or ":hidden-" in p.placement_id or
             ":reinforcement-059m:" in p.placement_id)]
    boards=sorted((p for p in mobile if ":board:" in p.placement_id),key=lambda p:p.placement_id)
    hidden=sorted((p for p in mobile if ":hidden-" in p.placement_id),key=lambda p:p.placement_id)
    patches=sorted((p for p in mobile if ":reinforcement-059m:BOARD33-" in p.placement_id),key=lambda p:p.placement_id)
    beams=sorted((p for p in mobile if ":reinforcement-059m:T" in p.placement_id),key=lambda p:p.placement_id)
    assert tuple(map(len,(boards,hidden,patches,beams)))==(21,9,2,2)
    postponed=[by[JOINT+n] for n in ("03","04","05","06")]
    postponed.append(by[PARAPET])
    postponed+=sorted([p for p in parts if
        (p.placement_id.startswith(PREFIX) and ":rail-" in p.placement_id)
        or "west-return-rail:cross-joint" in p.placement_id],
        key=lambda p:(p.z_plates,p.placement_id))
    assert len(postponed)==47
    assert not {p.placement_id for p in mobile}&{p.placement_id for p in postponed}
    return boards,hidden,patches,beams,postponed

def build(bundle):
    model=bundle.brick_model
    boards,hidden,patches,beams,postponed=ordering(model)
    by={p.placement_id:p for p in model.parts}
    moved_ids={p.placement_id for p in boards+hidden+patches+beams+postponed}
    assert len(moved_ids)==81
    old=bundle.assembly_plan
    assert old.total_parts==1894
    kept=[]
    for s in old.steps:
        ids=[pid for pid in s.placement_ids if pid not in moved_ids]
        if ids:
            kept.append(s.model_dump(mode="python") | {"placement_ids":ids,"z_plates":min(by[x].z_plates for x in ids)})
    assert sum(len(s["placement_ids"]) for s in kept)==1813
    pos=next(i for i,s in enumerate(kept) if s["phase"]=="Fenêtres")
    before,after=kept[:pos],kept[pos:]
    posts={p.placement_id for p in model.parts if p.placement_id.startswith(PREFIX)
           and "support-solution:timber-post" in p.placement_id}
    assert len(posts)==36 and posts<={pid for st in before for pid in st["placement_ids"]}
    exterior_bag=next(s.bag for s in old.steps if s.phase=="Structures extérieures")
    custom=[]
    def add(parts,title,kind="subassembly"):
        assert parts
        custom.append(dict(component="facade_detail",z_plates=min(p.z_plates for p in parts),
                           title=title,placement_ids=[p.placement_id for p in parts],
                           phase="Structures extérieures",bag=exterior_bag,
                           instruction_kind=kind,focus="closeup",view="perspective"))
    for i in range(3):
        add(boards[i*7:(i+1)*7],f"059N Préassembler les planches face inférieure visible — lot {i+1}/3 (maintien manuel)")
    add(hidden,"059N Fixer 9 plaques cachées sous les planches, dont 029:06 sous board:00001")
    add(patches,"059N Placer deux PLATE_1X3 sous board:00027 et board:00033 — liaison nominale")
    add(beams,"059N Ajouter les traverses T1/T2 puis maintenir, retourner et descendre le plancher COMPLET sur les poteaux")
    assert sum(len(s["placement_ids"]) for s in custom)==34
    for n,p in enumerate(postponed,1):
        name=("liaison béton-bois" if n<=4 else "parapet voisin" if n==5 else "garde-corps/raccord")
        add([p],f"059N APRÈS descente du module — pièce {n:02d}/47 ({name}): {p.placement_id}",kind="placement")
    all_entries=before+custom+after
    steps=[AssemblyStep(**(dict(s)|{"sequence":i,"step_id":f"step-{i:04d}"}))
           for i,s in enumerate(all_entries,1)]
    plan=AssemblyPlan(building_id=model.building_id,volume_id=model.volume_id,
                      total_steps=len(steps),total_parts=1894,
                      total_bags=old.total_bags,steps=steps)
    actual=[pid for s in plan.steps for pid in s.placement_ids]
    assert len(actual)==len(set(actual))==1894 and set(actual)==set(by)
    special_steps=[i for i,s in enumerate(plan.steps) if s.title.startswith("059N")]
    assert len(special_steps)==53
    assert special_steps==list(range(special_steps[0],special_steps[0]+53))
    return plan,postponed

def run(source=ORIGINAL,preview=PREVIEW,output=OUTPUT):
    canonical=(source/"brick-model.json").read_bytes()
    old=json.loads(canonical)
    assert len(old["parts"])==1890
    bundle=BrickExportBundle.model_validate_json((preview/"viewer-export-reinforced.json").read_text(encoding="utf-8"))
    assert len(bundle.brick_model.parts)==1894
    assert [p.model_dump(mode="json",exclude_none=True) for p in bundle.brick_model.parts[:1890]]==old["parts"]
    plan,postponed=build(bundle)
    staged=bundle.model_copy(update={
        "assembly_plan":plan,"instruction_plan":generate_instruction_plan(plan),
        "bag_plan":generate_bag_plan(plan)})
    staged=BrickExportBundle.model_validate(staged.model_dump(mode="python"))
    assert staged.bom.total_parts==staged.assembly_plan.total_parts==1894
    assert staged.instruction_plan.total_parts==staged.bag_plan.total_parts==1894
    notes={
        "model_status":"APPROVED_REINFORCEMENT_PREVIEW_NOT_YET_CANONICAL",
        "original_parts":1890,"reinforced_parts":1894,
        "floor_preassembled_parts":34,"floor_boards":21,
        "hidden_old_plates":9,"new_plates_1x3":2,"new_beams_1x8":2,
        "post_segments_preinstalled":36,"deferred_placements":47,
        "deferred_ids":[p.placement_id for p in postponed],
        "staged_instruction_steps":plan.total_steps,
        "geometry_stud_grid":"NOMINAL_ONLY",
        "lowering_clearance":"AABB_PASS",
        "physical_clutch":"NOT_CERTIFIED",
        "manual_holding":"NOT_CERTIFIED",
        "roof_or_nonrectangular_access":"NOT_CERTIFIED",
        "assembly_order":[
          "Build 36 existing support-post segments per baseline instructions.",
          "Lay out 21 floor boards face-down on a workbench; provisional support needed.",
          "Mate 9 original hidden plates underneath boards, particularly 029:06 to board:00001.",
          "Install 2 additional hidden PLATE_1X3 connectors underneath 00027/00033.",
          "Install 2 additional BRICK_1X8 beams T1 and T2.",
          "Hold the 34-part module, turn upright and lower vertically onto posts.",
          "After lowering install 4 concrete/timber joint bricks, 1 parapet, then 42 rail/cross-joint pieces.",
        ],
        "limitations":"No physical clutch, gripping, load-bearing, manual insertion or part/color certification.",
    }
    output.mkdir(parents=True,exist_ok=True)
    (output/"viewer-export-staged-1894.json").write_text(staged.model_dump_json(indent=2,exclude_none=True),encoding="utf-8")
    (output/"staged-terrace-guide.json").write_text(json.dumps(notes,indent=2,ensure_ascii=False),encoding="utf-8")
    lines=["# BOLDÜNGO — Terrasse renforcée (notice de montage PROVISOIRE)","",
           "**34 pièces préassemblées, puis 47 pièces à installer après pose du plancher.**",
           "**1894 pièces dans la variante proposée ; 1890 pièces dans la base inchangée.**",
           "**Les contacts et trajectoires contrôlés sont géométriques, pas une preuve de résistance physique.**","",
           "## Étapes pratiques (sous réserve d’essai réel)",""]
    lines.extend(f"{i}. {desc}" for i,desc in enumerate(notes["assembly_order"],1))
    lines.extend(["","## Les 47 pièces différées, dans l’ordre vérifié",""])
    for n,p in enumerate(postponed,1):
        lines.append(f"{n:02d}. {p.placement_id} — {p.part_id} ({p.x_studs},{p.y_studs},{p.z_plates}), rotation {p.rotation_quarter_turns}.")
    lines.extend(["","## Points bloquants avant certification","",
                  "- Les 26 contacts de plancher encore hors des familles VALID documentées.",
                  "- Les fixations sur poteaux à un seul tenon et le maintien de la planche 00033.",
                  "- Les tolérances et la manutention d’un bloc de 34 pièces restent non testées physiquement.",
                  "- Les coloris/disponibilités des pièces restent à vérifier.",
                  "- Ne pas fusionner ni déployer cette notice comme étant physiquement certifiée."])
    (output/"staged-terrace-guide.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    assert (source/"brick-model.json").read_bytes()==canonical
    print(json.dumps({k:notes[k] for k in ("original_parts","reinforced_parts","floor_preassembled_parts","deferred_placements","staged_instruction_steps","physical_clutch")},indent=2))
    return staged,notes

if __name__=="__main__":
    run()
