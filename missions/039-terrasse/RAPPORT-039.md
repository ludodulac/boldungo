# 🧱 BOLDÜNGO — M039 : TERRASSE (CONSTRUCTION 4)

**HEAD vérifié avant M039 :** `f4f7731085594db62bc26d430fc0affebc50d033`. Travail exclusivement dans `feat/boldungo-parallel-035-terrasse`, PR **#944 DRAFT**.

## Niveaux et preuve propriétaire

Le propriétaire a confirmé : **la terrasse bois est plus basse que le plateau béton et reliée par une seule marche**, hauteur non mesurée. L'ancienne Scene modélise la plateforme béton à **2,62 m**, la terrasse bois à **2,82 m** : inversion. Dans le LDraw B3 : dessus béton à **y = −288 LDU** et bois à **y = −312 LDU**, bois placé 24 LDU trop haut. La variante indépendante abaisse uniquement le bois de **+48 LDU sur l'axe Y**, portant le bois à **−264 LDU**, soit **24 LDU plus bas** que le béton. Cette valeur est une **hypothèse expérimentale** et non un relevé de la marche. Les **1 904 pièces B3 sont intactes**.

## Variante et matériel

La nouvelle copie compte **164 pièces** : 46 pièces béton originales, 102 pièces bois/reprises B2 descendues, 16 pièces nouvelles. Pour ne pas prolonger les poteaux sous le terrain, **six éléments supérieurs de poteaux sont retirés dans cette seule copie**, ainsi que l'ancien pontage B3 (raccord rendu invalide par le changement de niveau). L'ancien prototype M035 de **171 pièces reste disponible sans modification**.

Le Y n'est plus fait en gradins : **deux poutres inclinées Technic 32524 à sept trous** rejoignent trois **briques Technic 3700** par trois **broches 6558 de 3L**. Le pied comporte une brique 3001, cinq briques 3004 et deux plaques 3023b. Les deux bras décrivent une pente **4:3**, choisie pour 5 intervalles de trous, **pas mesurée sur la maison**. L'axe de perçage 32524 local Y et l'axe de broche 6558 local X vérifiés en M098 sont transportés au même Z mondial ; `3700.dat` a l'axe du trou local Z. Les centres de trous sont donc géométriquement coaxiaux. Aucun serrage, passage de collerette, résistance au cisaillement ni montage au sol n'est prouvé.

## Contacts et conflits

Les **8 contacts tenons** entre briques/plaque du pied et la fourche sont nominaux sur grille 20 LDU. Les deux briques hautes 3700 ont des contacts géométriques sous le vrai tablier B3 abaissé, donnant **7 correspondances de planches**. **Attention : plusieurs planches B3 se chevauchent déjà**, ces 7 correspondances ne constituent ni 7 attaches indépendantes ni un plancher assemblable ; les résultats M035 étaient fondés sur une projection simplifiée et ne prouvaient pas ces contacts au bon axe. 

Le test AABB des nouvelles briques orthogonales du Y ne décèle **0 recouvrement nouveau** ; en revanche, le bois abaissé présente **12 collisions AABB** avec d'autres éléments laissés en place dans B3 (voir `AUDIT-039.json`). Les poutres et broches ne sont pas certifiées par contrôle maillé ni balayage d'insertion. Le terrain et la solidité ne sont pas vérifiés. **L'ensemble est bloqué et ne doit pas être présenté comme prêt à monter.**

Sources photo : les observations Survey de `LEFT_001.jpg` et `LEFT_002.jpg` attestent plateforme bois, poteaux et contreventements, mais les JPG binaires n'ont pas été directement inspectables par l'outil GitHub ; l'emplacement et les angles exacts restent inconnus.

## Fichiers

- `PROTO-039-TERRASSE-Y-TECHNIC.ldr` — LDraw indépendant.
- `BOM-039.json` — inventaire exact.
- `AUDIT-039.json` — niveaux, axes, contacts, 12 collisions.
- `APERCU-039.svg` — vues du profil béton/bois et du Y incliné.
- `VERIFIER-039.py` — test ciblé autonome, sans modification du moteur.
- `.github/workflows/boldungo-terrasse-039.yml` — CI ciblée de cette branche.

**Décision : le Y incliné nominal est construit, mais la correction des niveaux laisse 12 conflits ; stabilité et insertion restent NON CERTIFIÉES. Aucune fusion ni publication.**
