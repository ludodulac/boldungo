# 🧱 BOLDÜNGO — R-1 — TOITURE LEGO DOCUMENTÉE (MISSION 1/3)

> Une **notice LEGO existante** est l'autorité sur *son montage officiel*.
> Le toit expérimental R-1 est une **adaptation nouvelle**, qui n'en hérite
> PAS automatiquement de la preuve d'insertion, de rigidité ou de stabilité.

## FAIT VÉRIFIÉ : une véritable notice officielle

**Set :** LEGO Creator 3-en-1 **#31009, La petite maison / Small Cottage** (2013, 271 pièces annoncées par LEGO).

**Notice exacte :** livret **1/3**, imprimé **31009_BI_BK1**, fichier LEGO **6038244.pdf**.

- Fiche officielle : https://www.lego.com/fr-fr/service/building-instructions/31009
- PDF officiel original : https://www.lego.com/cdn/product-assets/product.bi.core.pdf/6038244.pdf
- Références des pièces du set (pour identifier les moules, PAS source normative d'insertion) : https://www.bricklink.com/catalogItemInv.asp?S=31009-1

Pages imprimées et opérations de toiture **vues directement dans le PDF LEGO** :

| Page de la notice | Étape LEGO | Opération observée |
|---|---|---|
| **47–48** | 1–3 | Constituer une base de plaques puis des supports/briques sous le premier bord de toiture. |
| **49** | **4–5** | Placer des briques longues inclinées bleu foncé, série de 45°, sur le sous-ensemble de support. |
| **51** | **7–8** | Construire les appuis des prochains éléments inclinés, sur les plaques de base. |
| **53** | **11** | Poser la première bande de briques inclinées sur le pan opposé : DEUX pans distincts. |
| **55** | **13** | Compléter les longueurs inclinées et les supports entre les pans. |
| **57** | **15** | Continuer les supports intérieurs avant de fermer. |
| **60** | **18** | Compléter les pans inclinés avec des briques 45° complémentaires. |
| **61–64** | **19–22** | Ajouter les supports de la ligne haute, puis les nouvelles pièces de toiture au-dessus. |
| **65–68** | **23–25** | Monter les pentes du petit volume de lucarne et terminer autour du faîtage. |

Les pages ci-dessus sont **les numéros imprimés** sur la notice. Dans le PDF, la page affichée peut être décalée d'une unité : page imprimée 49 = index PDF 48 (page 49 en comptage humain).

**Pièces officielles pertinentes (identifiées dans l'inventaire du set et dans les fichiers LDraw officiels) :**

| Moule LDraw | Fonction | Emploi R-1 |
|---|---|---|
| `4445.dat` | Vraie brique inclinée 45° **2 × 8**, notamment présente en bleu foncé dans le set 31009 | 4 éléments de couverture |
| `3037.dat` | Brique inclinée 45° 2 × 4, présente dans le set | Variante connue, non utilisée dans R-1 |
| `3038.dat` | Brique inclinée 45° 2 × 3, présente dans le set | Variante connue, non utilisée dans R-1 |
| `3039.dat` | Brique inclinée 45° 2 × 2, présente dans le set | Variante connue, non utilisée dans R-1 |
| `3007.dat` | Brique droite 2 × 8 | 4 supports longitudinaux **de notre adaptation** |
| `3003.dat` | Brique droite 2 × 2 | 28 piliers **de notre adaptation** |
| `3022.dat` | Plaque droite 2 × 2 | 4 fermetures de faîtage **de notre adaptation** |
| `3811.dat` | Baseplate 32 × 32 | 1 support de l'expérience |

**Ne pas prétendre que `3007/3003/3022/3811` à ces positions sont tirées de LEGO 31009** : ces supports et le faîtage sont une autre recette. Seule la méthode de *rangées de briques inclinées 45° sur une structure de briques et de plaques*, suivie de la fermeture du faîtage, vient du montage officiel.

## ADAPTATION R-1 : prototype physique virtuel

Script : `scripts/experiment_official_roof_r1.py`.

Modelé **sans aucune donnée de la maison de Ludo**.

**Largeur : 8 tenons, longueur 8 tenons** pour le premier module. Paramètre `--length-studs 16` pour répéter le même motif longitudinal 2 × 8 ; la largeur reste **FIXE** à 8 tenons dans ce prototype. Une adaptation à une autre largeur est un travail distinct et une hypothèse, pas encore une recette universelle.

La toiture contient :
- Pan gauche : 2 briques 4445 le long de la pente, avec pannes/briques empilées indépendantes.
- Pan droit : 2 briques 4445 symétriques.
- Les rangs hauts sont décalés d'une hauteur de brique (3 plaques), ils ne constituent pas une surface parfaitement lisse ; cette discrétisation est explicitement acceptée pour l'expérience.
- Faîtage : 4 plaques 3022 de 2 × 2, couvrant la jonction longitudinale des deux pans.
- Structure : 4 briques 3007 en pannes, 28 briques 3003 sous les quatre pannes et une baseplate 3811.

### Nomenclature **exacte du prototype R-1**, pas du set officiel

**41 pièces : 28 × 3003, 4 × 3007, 4 × 4445, 4 × 3022, 1 × 3811.**

Fichiers pérennes :
- `missions/R1/R1-31009-EXPERIMENT.ldr` — **modèle réel LDraw à 41 positions**, exportable.
- `missions/R1/BOM.json` — vraie nomenclature.
- `missions/R1/ORDER.json` — séquence d'insertion **proposée, non certifiée**.
- `artifacts/lego2-r1-official-roof/` — sorties CI dont audit JSON des vraies géométries, sauvegardées par GitHub Actions.
- `scripts/probe_official_roof_r1.py` — contrôles de quelques interfaces avec les vraies primitives `stud4a` et `stud`, coordonnées officielles et `check_collision` préexistant.

Ordre :
1. Baseplate.
2. Quatre groupes de piliers (deux rangs × deux pans), par niveaux successifs.
3. Quatre pannes 3007 sous les pans.
4. Pans : d'abord les deux rangées basses, puis les deux rangées hautes.
5. Plaques de faîtage 3022, par sections longitudinales.

La notice 31009 confirme la **méthode de pose LEGO officielle à rangs multiples**. L'ordre exact des pièces du **prototype**, qui possède un soubassement différent et pas de lucarne, **n'est pas directement validé par la notice**.

## VÉRIFICATIONS : ne pas surpromettre

Deux niveaux distincts :
1. **Graphe nominal :** toutes les 41 pièces sont dans une composante nominale enracinée dans la baseplate, chaque pièce de toiture possède au moins un parent ; nombre de liens vérifié par tests. C'est seulement une *coïncidence de coordonnées*.
2. **Vraie géométrie LDraw :** `4445.dat` contient sept références à `stud4a.dat` ; le support longitudinal `3007.dat` offre deux rangées de huit tenons. La vérification R-1 calcule les **sept centres de cavités** face aux tenons et leur profondeur d'engagement et contrôle les **interfaces sélectionnées** contre les triangles LDraw. Elle consigne les collisions observées sans les cacher.

Ce programme **ne démontre pas** l'insertion continue de chaque pièce, l'absence de collisions sur toutes les paires, ni la résistance physique de la toiture. Aucun nouveau moteur général créé.

## HYPOTHÈSE

Remplacer les briques 18° expérimentales par la famille 45° `4445/3037/3038/3039` déjà employée et assemblée dans une vraie notice LEGO réduit le risque *conceptuel*. La reproduction exacte du mécanisme LEGO 31009 pourrait être encore plus sûre que l'adaptation aux supports sur piliers ; **la conception R-1 n'est pas équivalente à celle du set**.

## RECOMMANDATION

Évaluer le **modèle LDraw de 41 pièces** et la sortie de géométrie CI. En cas de collision statique ou de raccord inconnu, conserver l'artefact et l'indication, ne pas réécrire la notice LEGO ni affirmer que la famille 45° est incompatible. Si les appuis se montrent plausibles, une prochaine mission R-2 pourrait adapter **la base/support exact du set**, mais **R-2 ne commence pas ici** et ne doit pas toucher GUIDED-004.

**Chantier A = terminé ; PR #929 préservée ; chantier R limité à 3 missions, ici R-1 uniquement.**
