# 🧱 BOLDÜNGO — MISSION A-3 : BILAN FINAL DU CHANTIER A (2026-10-24)

> **Décision technique : STOPPER LA VALIDATION ET LA TRANSPOSITION À A1 EN L'ÉTAT.**
> Le petit toit 3022 de 24 pièces est préservé. Il n'est PAS encore prouvé assemblable de bout en bout, mais **aucune incompatibilité fondamentale des pièces n'a été démontrée**. Cette décision ferme A-1/A-2/A-3 ; aucune mission A-4 automatique, aucune fusion, aucun GUIDED-004.

## FAIT VÉRIFIÉ

**Reprise :** `AI_START_HERE.md`, Grand-père, `PROJECT_PRINCIPLES.md` relus. Au début d'A-3, `main=b82f94cc2e7ad2d8d613d5eb0d610fb42cdf7fc9` et branche LEGO2 `3cb6b897f29b6e44e312cd46220903ed6f9e363a`. PR #929 toujours DRAFT. La CI A-2 #40106019091 et la CI générale #40106019087 étaient SUCCESS sur `f6040e236751cb91cef5daeb171e8bef631a7054`.

**Modèle inchangé :** `A2-MODULE-3022-PROPOSE.ldr`, 24 pièces, 18×`3003`, 4×`30363`, 1×`3022`, 1×`3811`, deux pans / deux rangs par pan, quatre colonnes de fondation.

**Vérificateur ciblé :** `scripts/verify_small_roof_a3.py` lit directement les primitives LDraw officielles téléchargées dans GitHub Actions, depuis le miroir au SHA figé `c43ed06a128a10ed65675166bf42eb6fd608b9b0` ; ni nouvelle famille de toit, ni moteur de collision général.

### Connexions GEOMÉTRIQUEMENT établies à la position finale

Le rapport `A3-FINAL-STATIC-SEATS-AND-INSERTION.json` examine **23 sièges géométriques** (une pièce autre que la baseplate par siège) et **24 liens directs parent→enfant** (le faîtage porte sur DEUX pans). Les validations exigent simultanément :
1. existence effective de `stud.dat` / `stud4.dat` / `stud4a.dat` dans les fichiers officiels, transformés en coordonnées mondiales par les matrices LDraw du modèle ;
2. **QUATRE vrais tenons** entourant le tube central, aux décalages `(±10,±10)` LDU par rapport à son centre ;
3. rayon du tenon **6 LDU**, rayon extérieur du tube **8 LDU**, écart nominal `sqrt(200)-14 = 0,1421356 LDU` (>0), enceinte intérieure des quatre murs à `±16 LDU` ;
4. **pénétration verticale d'environ 4 LDU** (pas une simple coïncidence des centres) : `3003` bouche locale Y=24, `30363` tube central `stud4a` bouche locale Y=23,968 (arrondi LDraw), `3022` bouche Y=8 ;
5. `CONTACT` sans `COLLISION` du maillage officiel à la position finale pour les paires autres que la baseplate, et correspondance explicite à la grille officielle `3811` pour les quatre premières briques.

**Résultat : 23/23 sièges statiques démontrés, dont 5/5 connexions de toiture ; 24 liens de support ; 4/4 raccords de pilier à la baseplate validés dans le périmètre des primitives de tenons/tubes ; 0 pièce sans chemin d'appui statique démontré ; 1 composante du graphe nominal.**

Les primitives officielles `s/3003s02.dat`, `s/30363s01.dat`, `3022.dat`, `3811.dat`, `stud.dat`, `stud4.dat`, `stud4a.dat`, `stug-2x2.dat` et `stug-8x8.dat` fournissent ces géométries ; les transformations des 24 placements sont extraites des lignes `type-1` du LDraw.

**Fondations :** le maillage officiel de `3811` indique une enveloppe verticale Y de -4 à +4 LDU. Les 19 pièces qui ne se connectent pas directement à la baseplate sont séparées verticalement de celle-ci ; les quatre briques de départ sont vérifiées via sa grille officielle de tenons et le tube des `3003`. Il n'y a toujours PAS de `check_collision` triangle-à-triangle exhaustif contre tous les triangles de l'énorme baseplate. Cette limite est maintenue explicitement.

### Ordre d'assemblage et insertion continue

L'ordre conservé couvre **24 pièces** : baseplate → briques `3003` par niveaux et quatre supports supérieurs → deux rangs de deux `30363` → `3022` de faîtage.

Le nouveau contrôleur de trajectoire va au-delà des huit échantillons A-2 :

- Pour toute translation verticale, un objet situé dans une projection XZ **disjointe** ne peut mathématiquement entrer en collision. Il en va de même lorsqu'il demeure entièrement **au-dessus** de l'objet fixe même à l'arrivée : cette séparation ne peut que s'agrandir lors du déplacement vers le haut.
- Pour les seules pièces `3003` 2×2, l'emboîtement axial de 4 LDU avec quatre tenons et un tube vertical prismatique (`stud4.dat`) est établi par les profils rayonnants officiels, les limites de coque et la position des pièces. La preuve de leurs trajectoires est conditionnée à l'absence démontrée de toute autre pièce fixe dans le volume balayé.
- Les **quatre `30363` et la `3022`** ne disposent pas d'une preuve de balayage continu complète. Le programme ne substitue pas un échantillonnage fin ou un `CONTACT` statique à cette exigence ; il retourne `NON_DEMONTREE`.

**Bilan d'insertion sur l'assemblage de 23 pièces : 18 briques standard `3003` couvertes par la preuve analytique verticale limitée ; 5 pièces de toiture NON DÉMONTRÉES en insertion continue.** Par conséquent l'assemblage global complet reste `NOT_CERTIFIED` et `full_assembly_geometrically_proven=false`.

Le contrôle final A-2 de toutes les **253 paires hors baseplate** a trouvé **0 collision statique détectée** avec `3022`; le statut des collisions sur les cinq trajectoires inconnues ne peut pas être conclu par extrapolation.

### Régression négative obligatoire

Le test `test_bad_20_ldu_shift_cannot_pass_as_valid_stud_tube_seat` déplace délibérément un `30363` de **20 LDU (un tenon)** sans déplacer son porteur `3003`. Le vérificateur doit répondre `INCOMPATIBLE`, rendre le raccord `real_official_tube_and_studs_fit=false` et couper la chaîne d'appui statique de cette pente et du faîtage. Un simple test `CONTACT` ou un graphe nominal n'offre pas cette garantie.

Les tests nécessitant la bibliothèque DAT épinglée tournent intégralement dans le CI spécialisé ; ils sont marqués `skip` dans le CI général qui ne possède pas cet ensemble, pour ne pas déclarer un faux échec sans fichiers. Les anciens 14 tests restent actifs et le CI spécialisé exécute en outre les trois tests A-3.

### Commandes de reproduction

```bash
python -m pytest -q tests/bricks/test_stacked_roofs_a.py tests/bricks/test_small_roof_a2.py
python scripts/download_ldraw_probe_066.py /tmp/mission-a-ldraw --max-files 240 --parts 30363 3007 3003 3023b 3008 3811 3022
python scripts/verify_small_roof_a2.py --ldraw-root /tmp/mission-a-ldraw --output artifacts/lego2-a2-small-module
A3_LDRAW_ROOT=/tmp/mission-a-ldraw python -m pytest -q tests/bricks/test_small_roof_a3.py
python scripts/verify_small_roof_a3.py --ldraw-root /tmp/mission-a-ldraw --output artifacts/lego2-a2-small-module/3022/A3-FINAL-STATIC-SEATS-AND-INSERTION.json
cmp missions/A/A2-MODULE-3022-PROPOSE.ldr artifacts/lego2-a2-small-module/3022/SMALL-ROOF-A2.ldr
```

L'historique des runs de la PR #929, leurs journaux et leurs artefacts constitue la source des sorties brutes et CI ; **ne pas attribuer un SUCCESS à un HEAD nouveau tant que ses deux workflows ne sont pas terminés avec succès**.

## HYPOTHÈSE

Les briques `30363` posées sur `3003` et le faîtage `3022` constituent une **architecture géométriquement plausible** : connexions statiques avec profondeur de pénétration vérifiée, chaîne de fondation documentée, aucune collision statique détectée hors baseplate.

**Non prouvé :** aucun des cinq mouvements continus de toiture. La position finale géométriquement compatible n'entraîne ni la possibilité d'y arriver ni une résistance physique. Les tests LDraw ne prouvent ni tolérances d'injection, ni friction réelle, ni stabilité à long terme.

## RECOMMANDATION — décision finale unique

### **STOPPER la certification de cette méthode et toute généralisation à A1 avec les moyens de ce chantier.**

Ce STOP signifie : **fin du chantier expérimental A dans la limite stricte des trois missions** et refus de promouvoir un toit partiellement vérifié dans le générateur. **Ce n'est pas une preuve que les pièces LEGO sont incompatibles.**

Une poursuite humaine distincte serait justifiée uniquement après décision explicite de Grand-père et Ludo, et disponibilité d'une méthode CAD/swept-volume capable de trancher **les cinq seules trajectoires de toiture**. Une telle décision serait un **nouveau périmètre autorisé** ; ce rapport n'ouvre pas de mission A-4 ni de mission B.

### Trois missions — bilan

- **A-1** : trois petites maisons A1/A2/A3 (195/313/431 pièces ; 80/120/140 toiture), graphes nominaux, faîtage 3023b signalé `COLLISION` ; pas de preuve N5/N6.
- **A-2** : micro-toit réellement exporté de 24 pièces ; remplacement par 3022, 0 collision statique détectée hors baseplate sur 253 paires ; premières positions d'insertion seulement sondées.
- **A-3** : audit unitaire des tenons, tubes et profondeur réelle pour les 23 sièges / 24 liens ; connexion de la baseplate par primitives et limites géométriques ; test volontairement impossible rejeté ; preuve continue limitée aux 18 empilements standard, **5 poses de toiture indéterminées**.

**Questions finales :** (1) cinq sièges statiques toiture OUI ; (2) baseplate raccords 4/4 par géométrie primitive OUI ; (3) toutes les insertions continues NON ; (4) 0 siège statique non démontré, 5 insertions de toiture non démontrées ; (5) 0 pièce sans chemin d'appui statique démontré, 5 éléments toiture sans chemin d'assemblage continu démontré ; (6) 0 collision statique détectée hors baseplate, absence sur les trajets continus NON CONCLUE ; (7) toit complètement assemblable : NON DÉMONTRÉ ; (8) généralisation A1 : NON ; (9) STOPPER LE CHANTIER A et préserver le module sans fusion.

**Aucune modification de `main`, de la branche LEGO2 principale, de GUIDED-004 canonique ou des anciens modules. PR #929 maintenue DRAFT.**
