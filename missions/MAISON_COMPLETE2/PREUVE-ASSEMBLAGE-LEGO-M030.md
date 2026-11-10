# BOLDÜNGO — Mission 030 — Preuve d'assemblage par notice LEGO

**Verdict : B — ASSEMBLAGE DIFFÉRENT DOCUMENTÉ.** Une notice authentique LEGO illustre la fixation d'une pente `30363` sur une plaque LEGO à tenons. **Aucune notice examinée ne démontre explicitement le montage exact de `roof-000048` sur l'unique tenon disponible de `gable-000006` (`3004.dat`) à son site local (10,24,0).**

## 1. Intégrité des sources et sélection

- Modèle original B3 **strictement inchangé** : `missions/B3/generated/GUIDED004-B3-1904.ldr`, blob SHA `288c60fde76918128d8b955f78ebfa9afc2dfe8e` ; 1 904 pièces dont 408 `30363.dat`.
- Pièce recherchée **30363** = `Slope 18 4 × 2` = `ROOF TILE 2X4X1, 18°`. **Ne pas confondre avec le SET LEGO 30363 « Race Boat »**, qui n'est pas la référence de la pente.
- Bibliothèque de références : [catalogue BrickLink 30363](https://www.bricklink.com/v2/catalog/catalogitem.page?P=30363) ; [fiche Brick Architect 30363](https://brickarchitect.com/parts/30363) ; [catalogue LDraw officiel 30363.dat](https://library.ldraw.org/parts/list?tableSearch=30363.dat).
- Recherche bornée à **quatre livrets officiels** ; seuls les passages visuellement inspectés sont qualifiés de preuves. Aucun audit des 408 pentes / 1 904 paires ni nouveau contrôle de collision.

## 2. Notices LEGO réellement consultées

| Set LEGO | Notice officielle | Pages / étapes vérifiées | Ce qu'elle établit réellement |
|---|---|---|---|
| **60249 — La balayeuse de voirie** (2020) | [PDF LEGO n°6305218](https://www.lego.com/cdn/product-assets/product.bi.core.pdf/6305218.pdf) ; [page LEGO](https://www.lego.com/fr-fr/service/building-instructions/60249) | **Page imprimée 13 / étape 6 :** pose de la plaque verte 4×8. **Page imprimée 16 / étape 9 :** placement de la pente gris clair 18° 4×2 sur la surface à tenons. **Page imprimée 17 / étape 10 :** pièces ajoutées autour de la pente déjà posée. | **Assemblage d'une vraie pente 30363 sur une plaque à tenons officiellement illustré.** Le support représenté est la plaque **3035** (4×8), pas la brique **3004** du B3. |
| **30495 — AT-ST** (2022) | [PDF LEGO n°6401256](https://www.lego.com/cdn/product-assets/product.bi.core.pdf/6401256.pdf) ; [page LEGO](https://www.lego.com/en-us/service/building-instructions/30495) | **Page PDF 1 (index 0), étapes 4 et 5 :** placement de la pente sur un sous-ensemble de cabine. | Autre exemple visuel d'utilisation de la pente du jeu `30495` ; le support détaillé et le point d'accroche exact ne peuvent pas être assimilés à la jonction 3004 du B3 à partir du seul dessin. |
| **31004 — Fierce Flyer / Le rapace** (2012) | [PDF LEGO n°6036221, livret 1](https://www.lego.com/cdn/product-assets/product.bi.core.pdf/6036221.pdf) ; [page LEGO](https://www.lego.com/en-us/service/building-instructions/31004) | Pages PDF indices **4, 10, 18 et 25** (pages imprimées 5, 11, 19, 26) examinées. | Aucun montage `30363` sur `3004` reconnu de manière vérifiable **dans les extraits consultés**. On ne conclut pas à son absence dans tout le livret. |
| **11014 — Bricks and Wheels / Briques et roues** (2021), **livret 2** | [PDF LEGO n°6349723, livret 2](https://www.lego.com/cdn/product-assets/product.bi.core.pdf/6349723.pdf) ; [page LEGO](https://www.lego.com/en-ie/service/building-instructions/11014) | Pages PDF indices **3, 16, 32 et 48** (imprimées 4, 17, 33, 49). | Aucun montage équivalent `30363/3004` identifié dans les pages examinées ; le livret 1 et les autres pages **ne sont pas déclarés épuisés**. |

### Vérification indépendante des références de la notice probante 60249

L'[inventaire de pièces du set officiel 60249 reproduit par BrickLink](https://www.bricklink.com/catalogItemInv.asp?S=60249-1&bt=0&sortAsc=A&sortBy=0&v=0&viewCodes=Y) et l'[inventaire Brickset](https://brickset.com/inventories/60249-1) identifient précisément :

- **`30363`**, pente `Slope 18 4 × 2` gris clair bleuté, **1 pièce** (élément LEGO `4211618` ou `4509915`).
- **`3035`**, plaque `Plate 4 × 8` verte, **1 pièce** (élément LEGO `4277361`).
- **`3004`** est également présent dans l'inventaire du set 60249, mais **la notice n'établit pas qu'il constitue le support direct sous la pente à l'étape 9**. Sa simple présence dans la boîte ne démontre aucune connexion `30363/3004`.
- La source LDraw `parts/3035.dat` précise aussi `0 Plate 4 x 8`, avec les vrais `stud.dat` aux centres sur grille 20 LDU ; `parts/30363.dat` est la pente 18°.

**Preuve LEGO au sens de la notice :** à l'étape 9, le constructeur pose la pente `30363` sur le sous-ensemble dont la grande plaque verte `3035` a été montée à l'étape 6. Cela documente une **solution de construction adoptée par LEGO**, mais ne donne pas, sans étude complémentaire, les tolérances de chaque tenon ou la certitude d'une insertion de l'unique tenon sous la pente de notre maison B3.

## 3. Comparaison avec la jonction réelle B3

| Propriété | B3 analysé M028–M029 | Notice LEGO 60249 (étapes 6 et 9) |
|---|---|---|
| Pente | `roof-000048`, `30363.dat` | `30363`, même famille de pente réelle |
| Support sous la pente | `gable-000006`, **brique `3004` (1×2)** | **Plaque `3035` (4×8)** et sous-ensemble préassemblé |
| Centre du tenon considéré | **(470, −792, 50)** LDU monde ; **(10,24,0)** LDU local pente | La notice indique visuellement une fixation sur plusieurs tenons de plaque ; elle **ne cote pas** un site local unique |
| Nombre de tenons de ce support en contact potentiel | **1 seul** sous l'empreinte de la pente ; autre tenon `3004` hors de l'empreinte | Maillage régulier de nombreux tenons, contexte d'appui plus large |
| Position/orientation relative | Transformations B3 exactes et conservées | Schéma de montage sur une plaque horizontale, **pas** une preuve que les transformations correspondent exactement à B3 |
| Type de preuve | M029 : poche théorique ; signal `COLLISION` durant l'engagement d'un tenon isolé ; **C indéterminé** | Notice LEGO : **montage différent documenté** ; n'annule pas la prudence de M029 |

### Verdict **B — ASSEMBLAGE DIFFÉRENT DOCUMENTÉ**

La notice 60249 montre une application réelle de la pente 30363 sur un support LEGO standard à tenons. **Elle ne prouve ni que `roof-000048` peut être retenue par `gable-000006`, ni que le montage B3 peut être inséré sans obstruction.** La distinction entre connexion visuellement illustrée, connexion nominale LDraw et certification matérielle est conservée.

## 4. Petit prototype séparé du B3

Fichier indépendant : `missions/MAISON_COMPLETE2/PROTOTYPE-LEGO-60249-30363-3035-M030.ldr`.

- Une plaque authentique `3035.dat` à (0,0,0) LDU, orientation identité ; une pente authentique `30363.dat` à **(−10, −24, 20)** avec rotation `[0,0,1 ; 0,1,0 ; −1,0,0]`.
- Exemple **sur grille LDraw**, volontairement distinct du montage B3. Cette pose place un tenon existant de la plaque au point monde **(−10,0,10)**, soit **(10,24,0)** dans le repère local de cette pente, **le même site local qui préoccupait M029**. Les autres tenons de la plaque fournissent un environnement de support plus large que `3004`.
- **Ce modèle de deux pièces n'est pas une retranscription au tenon près de la notice 60249**, car le PDF ne fournit pas les matrices numériques des placements. **C'est une représentation illustrative basée sur les références LEGO effectivement documentées.**
- Pas de test de collision ni certification d'insertion réalisée sur le prototype ; aucune validation physique ne peut être présumée.

## 5. Décision proposée pour la toiture

**Ne rien modifier dans B3.** Pour la mission future, évaluer **une** solution à appui plus large, fondée sur le montage **30363 sur plaque 3035** documenté dans la notice 60249 ; comparer ensuite le nombre de tenons engagés et l'encombrement réel avec l'architecture de la maison avant toute adaptation. Le recours à une plaque 3035 pourrait nécessiter de changer la structure de soutien : **cela n'est ni étudié ni autorisé en M030**.

**Aucun logement inférieur fictif ajouté au moteur ; aucune connexion `30363/3004` certifiée ; PR #931 DRAFT, PR #941 intacte.**
