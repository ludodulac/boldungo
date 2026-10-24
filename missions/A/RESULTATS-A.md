# BOLDÜNGO — MISSION A : RESULTATS MESURÉS

**Périmètre :** nouveau dossier expérimental `scripts/experiment_stacked_roofs_a.py`, distinct de GUIDED-004 (canonique 1 890 pièces) ; aucune écriture sur `main`, aucun ancien module supprimé. PR #929 DRAFT, **NE PAS FUSIONNER**.

## FAIT VÉRIFIÉ

Dans GitHub Actions spécialisé de la PR #929, la commande :

```bash
python -m pytest -q tests/bricks/test_stacked_roofs_a.py
python scripts/experiment_stacked_roofs_a.py --output artifacts/lego2-mission-a
python scripts/download_ldraw_probe_066.py /tmp/mission-a-ldraw --max-files 240 --parts 30363 3007 3003 3023b 3008 3811
python scripts/probe_stacked_roof_mesh_a.py --ldraw-root /tmp/mission-a-ldraw --output artifacts/lego2-mission-a/LDraw-REAL-MESH-SIX-PAIRS.json
```

a produit trois maisons LDraw à placements de **vraies références LEGO**, et 12 tests spécialisés réussis. Les quantités et interfaces orthogonales publiées ci-dessous ont été vérifiées dans le log réel du run #40100041154, confirmé sur le HEAD plus récent #40100268114 (celui-ci inclut aussi les trois vues SVG techniques).

| Maquette | Emprise (tenons) | Pièces totales | Pièces du toit (30363 + faîtage) | Pièces sans appui **nominal** | Composantes **nominales** | Collisions de boîtes **orthogonales** | Toit relié nominalement à la baseplate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A1 | 20 × 20 | 195 | 80 | 0 | 1 | 0 | 80 / 80 |
| A2 | 26 × 24 | 313 | 120 | 0 | 1 | 0 | 120 / 120 |
| A3 | 26 × 28 | 431 | 140 | 0 | 1 | 0 | 140 / 140 |

**Les 0 pièces « sans appui nominal » ne sont PAS des 0 pièces sans appui mécaniquement démontré.** Le graphe parcourt des plans de tenons sur une grille, pas la géométrie exacte d'accrochage de chaque pièce ni sa résistance. L'existence d'un chemin jusqu'à la baseplate est une proposition de chaîne de pièces, pas une preuve structurale N4.

### Sous-contrôle réel LDraw (6 paires, A1 seulement)

Récupération de **48 DAT** de la version figée `c43ed06a128a10ed65675166bf42eb6fd608b9b0` du miroir public LDraw, hors dépôt. `lego_geometry_engine` a testé les vrais triangles des six couples suivants :

| Contact étudié | Verdict du calcul LDraw |
| --- | --- |
| 30363 du 1er rang ↔ poutre porteuse | `CONTACT` |
| 30363 rang 1 ↔ rang 2 | `CONTACT` |
| Dernières pièces 30363 gauche ↔ droite | `CONTACT` |
| Dernier 30363 gauche ↔ plaque 3023b au faîtage | `CONTACT` |
| Dernier 30363 droit ↔ plaque 3023b au faîtage | **`COLLISION` : revue impérative** |
| Première pièce 30363 ↔ mur de pignon | `CONTACT` |

Pour les six paires, les **empreintes X/Z** du vrai maillage correspondent à celles du modèle (YES/TRUE). Le `COLLISION` côté droit peut représenter une interférence LEGO de stud/tube permise ou une véritable pénétration illégale ; le test ne sait **pas** trancher. Ne pas déclarer « zéro collision géométrique globale » : **seules les boîtes orthogonales sont globalement à zéro**, et **1 collision est signalée sur 6 vérifications de vrais maillages**.

### Fichiers et visibilité

Génération par la CI, dans `artifacts/lego2-mission-a` :
- `COMPARE-THREE-HOUSES.json` : tableau comparatif exploitable.
- `LDraw-REAL-MESH-SIX-PAIRS.json` : observations d'interfaces.
- Pour chaque A1, A2, A3 : un modèle `.ldr` complet, un `EVIDENCE.json`, un `BOM.json`, un `ASSEMBLY-ORDER.md` et un `ELEVATION-TECHNIQUE.svg`.

Téléchargement via les **artifacts** du run spécialisé GitHub Actions, depuis la PR #929. Les SVG sont des projections des placements réels X/hauteur dont la profondeur est aplatie ; elles ne prétendent pas montrer les maillages LDraw complets.

## HYPOTHÈSE

Les rangées de briques inclinées 30363 peuvent peut-être s'emboîter directement aux tenons de la rangée précédente sans charnière ni ferme Technic, si leurs cavités réelles et les orientations d'insertion le confirment sur toute l'architecture. Les 3 petites maisons sont **des prototypes numériques de placement**, pas des notices de montage humain validées.

Les rangs avancent de 3 tenons et montent de 3 plaques : pente moyenne **21,801°**, facette de `30363` **18,435°**. L'angle 22° est un compromis architectural proche, mais pas une unique pente lisse. Le paramètre `overhang` existe, mais toute valeur non nulle est actuellement refusée jusqu'à preuve supplémentaire.

## RECOMMANDATION

1. **Corriger ou classifier explicitement** la collision du faîtage côté droit par une analyse limitée à la paire `30363/3023b` avec les tubes/tenons officiels.
2. Vérifier la cinématique d'insertion des rangs et des pannes sur un petit module, puis la tenue de la rangée sans affirmer une résistance sans simulation ou test approprié.
3. En cas de preuve négative, **CHANGER D'APPROCHE**, ne pas multiplier de micro-missions de diagnostic. Respecter les **3 missions maximum** et laisser Ludo choisir CONTINUER / CHANGER / STOPPER.

État **N4/N5/N6 : non démontré, non certifié**, pas de commande de pièces, pas d'essai demandé à Ludo. Aucun portage sur la maison canonique à ce stade.
