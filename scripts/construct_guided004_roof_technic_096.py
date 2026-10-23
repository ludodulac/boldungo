"""Mission 096 — actual composite LDraw, support graph and conservative evidence."""
from __future__ import annotations
import argparse,hashlib,json
from collections import Counter
from pathlib import Path
from brickhouse.bricks.brick_model import BrickModel
from brickhouse.bricks.geometry_adapter import CANONICAL_LDRAW_PARTS
from brickhouse.bricks.roof_technic_transfer_096 import build_096
from brickhouse.bricks.technic_triangle_095 import PARTS095
from construct_guided004_hinged_roof_093 import PARTS,save_ldraw,draw_views
PARTS.update(PARTS095)


def main(source:Path,output:Path):
    original_bytes=source.read_bytes()
    sha=hashlib.sha256(original_bytes).hexdigest()
    model=BrickModel.model_validate_json(original_bytes)
    if len(model.parts)!=1936:
        raise ValueError("GUIDED004_091_SOURCE_MUST_HAVE_1936_PARTS")
    built=build_096(model)
    if hashlib.sha256(source.read_bytes()).hexdigest()!=sha:
        raise AssertionError("ORIGINAL_091_FILE_CHANGED")
    f=built["foundation"]
    pieces=built["articulated_parts"]
    r=built["report"]
    output.mkdir(parents=True,exist_ok=True)
    (output/"BRICKMODEL-096-FOUNDATION.json").write_text(
        f.model_dump_json(indent=2)+"\n",encoding="utf8")
    ld=save_ldraw(f,pieces,output/"BOLDUNGO-096-ROOF-TECHNIC-COMPOSITE.ldr")
    if ld["ldraw_mapped_brick_model_part_count"]+ld["articulated_ldraw_placed_parts"]!=r["new_total"]:
        raise AssertionError("COMPLETE_COMPOSITE_LDRAW_COUNT_MISMATCH")
    views=draw_views(f,pieces,output/"views")
    for page in (output/"views").glob("*.svg"):
        text=page.read_text(encoding="utf8")
        page.write_text(text.replace("BOLDUNGO 093","BOLDUNGO 096"),encoding="utf8")
    full=Counter(p["ldraw_id"] for p in pieces)
    foundation_mapped=0
    for p in f.parts:
        d=CANONICAL_LDRAW_PARTS.get(p.part_id)
        if d is not None and d.placement_kind=="standard":
            full[d.ldraw_id]+=1
            foundation_mapped+=1
    if sum(full.values())!=r["new_total"]:
        raise AssertionError("BOM_NOT_EXACT_TO_EXPORTED_LDRAW")
    (output/"BOM-096-FULL-EXACT.json").write_text(json.dumps({
        "piece_count":r["new_total"],
        "per_part_ldraw_exact":dict(sorted(full.items())),
        "delta_from_095":r["added_bom_ldraw"],
        "removed_from_095":{},
        "colors":"UNSPECIFIED",
        "release_for_purchase":False,
        "source091_sha256":sha},indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    proof={**r,"source091_sha256":sha,"views_count":views,
           "ldraw_source":ld,"foundation_mapped":foundation_mapped,
           "assembly_placed_real_parts":[p for p in pieces if p["placement_id"].startswith("096-")],
           "graph":built["graph"],
           "historical_variants_mutated":False}
    (output/"ROOF-TECHNIC-096-EVIDENCE.json").write_text(
        json.dumps(proof,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    plan="""# BOLDÜNGO 096 — candidat d'assemblage, **NON CERTIFIÉ**

Le composite LDraw comprend réellement les pièces ajoutées. L'ordre
ci-dessous est une **séquence prévisionnelle** : N5 NON PROUVÉ.

1. Construire les murs et appuis historiques 095, sans modifier les façades.
2. Installer seulement les 3700 murales fondées de 095, sur leurs deux tenons
   identifiés ; placer les 2780 murales et les extensions Technic.
3. Préassembler les deux triangles 5–12–13 de chaque ferme avec les 6558,
   sans réclamer de double broche dans un trou déjà occupé.
4. Avant de poser les panneaux, placer une vraie 3700 (deux tenons) sous
   l'ancien rail 3460 «negative» aux positions u=17.5 et 18.5.
   Son trou transversal est à 10 LDU sous sa face supérieure.
5. Présenter le bras 32524 de 7 trous entre le trou de la 3700 et
   le trou indexé de la poutre 32278. Deux broches 2780 sont représentées.
6. ARRÊT obligatoire si l'écart d'axes > 0 : aucune flexion inventée
   et aucun «clutch valide» sans tolérance documentaire et balayage de
   collerette. L'écart exact figure dans ROOF-TECHNIC-096-EVIDENCE.json.
7. Installer les rails de couverture et les deux pentes **22°** uniquement
   après validation indépendante de l'accessibilité des broches et des
   interférences locales, puis des chemins d'efforts.
8. La panne de faîtage, la charpente et les supports latéraux conservent
   leur architecture 094/095 ; aucune charge admissible n'est revendiquée.

N1: pièces identifiées, posées dans le modèle. N2: interfaces candidates,
axes parfois non coïncidents. N3: écran d'enveloppes seulement, sans
maillages complets. N4: aucune charge établie. N5: insertion non établie.
N6: NOT_CERTIFIED. Ne commander ni pièces ni notice finale sur cette base.
"""
    (output/"NOTICE-096-CANDIDAT-MONTAGE.md").write_text(plan,encoding="utf8")
    print("LEGO2_096_COMPOSITE_PARTS",r["new_total"])
    print("LEGO2_096_ANCHORED_TWO_WALL_TRUSSES",r["grounded_two_wall_frames"])
    print("LEGO2_096_ROOF_TO_TRUSS_CANDIDATES",r["roof_bracket_brace_candidate_chains"])
    print("LEGO2_096_EXACT_N2_ROOF_TO_WALL_PATHS",r["exact_coaxial_complete_chains"])
    print("LEGO2_096_LOAD_RATED_PATHS",r["documented_and_load_rated_roof_to_foundation_paths"])
    print("LEGO2_096_2L_PIN_INTERFACES_SCREENED",r["pin_insertion_axis_and_nominal_lengths_inspected"])
    print("LEGO2_096_COLLAR_SWEEPS_VERIFIED",r["pin_collars_verified"])
    print("LEGO2_096_VIEWS",views)
    print("LEGO2_096_CERTIFICATION",r["physical_certification"])
    for x in r["candidate_details"]:
        if x.get("new_parts") is None and "axis_residual_ldu" in x:
            print("LEGO2_096_FRAME",x["frame"],x["status"],
                  "hole_residual_LDU",x["axis_residual_ldu"])
    return proof


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--source",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    args=p.parse_args()
    main(args.source,args.output)
