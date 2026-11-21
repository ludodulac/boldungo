# LEGO2-083 — Trois techniques de faîtage, décision AVANT placement

## Décision d'ingénierie

La PR #910 (LEGO2-082) a introduit un filtre de conception « connecteurs d'abord ». Cette mission produit **trois modèles d'expérience indépendants**, compare leurs interfaces et choisit un **essai physique limité à 30 pièces**. Il n'y a **aucune** nouvelle analyse des mêmes trois collisions LDraw, **aucune** fermeture des maillages et **aucune** modification de GUIDED-004.

**Vérification nécessaire avant tout achat :** les références **3005** (brique 1×1), **3008** (brique 1×8) et **30363** (pente 18° 2×4 en grille) doivent correspondre aux pièces physiques disponibles. Le code utilise les mappings LDraw existants du dépôt. Couleurs et variantes restent à choisir avec l'utilisateur ; la BOM contient les quantités mais ne constitue pas encore une commande marchande.

## Comparaison constructive — étapes déterministes

| Technique | Principe d'assemblage | Filtre avant construction | Décision |
|---|---|---|---|
| A — Couronne centrale | 3005 au centre, tuile de faîtage 26603, deux 30363 | Sous-face de 26603 sur trois pièces non documentée, collisions déjà observées | **REJETÉE** pour conception automatique |
| B — Traverse + poutre longitudinale | Quatre piles de 3005, deux traverses 3008, trois longerons 3008, deux rehausses 3005 et poutre sommitale 3008 ; six 30363 d'essai **non connectées** | **26** liaisons nominales documentées dans l'ossature à **24** pièces ; six liaisons de couverture absentes | **RECOMMANDÉE UNIQUEMENT comme essai physique**, pas comme toiture viable |
| C — Deux demi-panneaux et plaque de joint | Une plaque 1×6 portée par 3005, deux pentes 30363 posées séparément | Sous-face 30363 → plaque non documentée | **REJETÉE** pour conception automatique |

Les 26 liaisons du châssis B sont classées d'après le validateur existant : elles **ne démontrent ni le serrage réel, ni la stabilité, ni une descente de charge certifiée**. Le montage complet B est expressément **REJETÉ** par le filtre de connexions : les six 30363 n'ont aucune interface approuvée vers le châssis.

## Liste exacte du mini-kit B (30 pièces)

| ID modèle | ID LDraw/LEGO de référence | Quantité | Usage |
|---|---|---:|---|
| BRICK_1X1 | **3005** | **18** | 16 briques pour quatre piles + 2 rehausses |
| BRICK_1X8 | **3008** | **6** | 2 traverses, 3 longerons, 1 poutre de faîtage |
| BRICK_SLOPED_18_4X2 | **30363** | **6** | 3 pentes de chaque côté, **à tenter sans forcer** |
| **TOTAL** | | **30** | |

Aucune tuile 26603 n'est incluse dans B ; son assemblage simultané à trois porteurs demeure non démontré.

### Montage de l'ossature (grille de tenons entière)

Axes : **X et Y** = tenons ; **Z** = plaques (trois plaques par hauteur de brique ordinaire). Les coordonnées ci-dessous désignent le coin d'insertion enregistré dans le modèle, pas un plan de contrôle mécanique.

1. **Quatre piles de quatre 3005** : chacune empilée à **z = 0, 3, 6, 9**, aux coordonnées XY **(0,0), (0,6), (4,0), (4,6)**. Total **16**.
2. **Deux traverses 3008**, longueur orientée **Y**, à **(x=0,y=0,z=12)** et **(x=4,y=0,z=12)**. Total **2**.
3. **Trois longerons 3008**, longueur orientée **X**, à **(0,0,15), (0,3,15), (0,6,15)**. Total **3**.
4. **Deux rehausses 3005** à **(0,3,18)** et **(4,3,18)**. Total **2**.
5. **Une poutre haute 3008**, longueur orientée **X**, à **(0,3,21)**. Total **1**.

Ce châssis de **24 pièces** constitue une expérience de cheminement nominal des connexions entre poteaux, traverses, longerons et faîtage.

### Deux groupes de pentes à essayer APRÈS le châssis

6. **Trois 30363 de côté négatif**, positions *expérimentales, non validées* : **(x=0,2,4 ; y=0 ; z=18)**, rotation 1.
7. **Trois 30363 de côté positif**, positions *expérimentales, non validées* : **(x=0,2,4 ; y=4 ; z=18)**, rotation 1.

**Ne pas appuyer ni forcer pour les faire entrer.** Les coordonnées de pente ne sont PAS une notice de montage autorisée ; elles signalent les zones à confronter **physiquement**, une pièce après l'autre. Si elles ne s'emboîtent pas naturellement, c'est un résultat **d'échec utile**, pas une invitation à modifier la toiture réelle.

### Relevé de l'utilisateur après le test

- Le châssis est-il assemblable sans torsion ni collage ?
- Les supports tiennent-ils debout, sans contact forcé ?
- Peut-on engager et retirer chaque 30363 de chaque côté sans force excessive ?
- Les deux versants sont-ils réellement reliés entre eux à un composant commun ? Si non, le test **échoue** comme faîtage.
- Le montage tient-il sans aide sous son propre poids ? (Ne pas en déduire sa capacité sous charge.)
- Si possible, communiquer des photographies des jonctions, face et sous-face.

**Critère de succès de ce jalon :** le prototype est imprimable/reproductible via BOM et positions exactes, l'ossature possède un graphe de 26 connexions nominales, les six interfaces manquantes sont explicites. **Le succès du montage réel exige encore l'essai physique de l'utilisateur.**

## Production d'un résultat exploitable

`python scripts/design_ridge_trials_083.py --output artifacts/lego2-083/ridge-trials.json`

Produit trois décisions, les 30 placements complets, une BOM et une liste des conditions d'arrêt. Les scripts et tests ne touchent jamais le modèle canonique.

**Statut mécanique général : NOT_CERTIFIED.** Aucune certification N1–N6 n'est attribuée à la toiture de GUIDED-004.
