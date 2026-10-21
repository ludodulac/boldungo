# LEGO2-087 — Première liaison CONÇUE entre deux pans (au lieu de trois pièces sans attaches)

## Pourquoi

Le prototype 083–086 représente une ossature nominale de 24 pièces, mais les six pentes 30363 restent **non connectées** au châssis : il ne constitue donc PAS une toiture constructible. Avant d'extrapoler vers un bâtiment complet, cette mission synthétise **un mini-assemblage de seulement trois véritables pièces**, qui doit **réellement tenir deux pentes sur une même brique** après un test utilisateur. Le test est distinct de la maison canonique.

## Deux petites variantes constructives, deux orientations

- **D0 — joint sans vide** : 2 × pente 30363 de directions opposées, + 1 × brique **3003** (2×2) posée à cheval sur la jonction : en grille canonique, les deux paires de tenons LDraw des pentes occupent les **quatre cellules distinctes sous la brique**.
- **D1 — joint avec vide d'un tenon** : 2 × 30363 + 1 × brique **3002** (2×3), dont la sous-face couvre les quatre tenons des pentes, avec un vide central. Variante de repli pour éviter que les corps des pentes se heurtent.
- Chaque variante est générée pour la direction de faîtage 0 **et** 1 (quatre expériences bornées) ; translations X/Y/Z possibles, pas de coordonnées dépendantes de GUIDED-004.

La vraie référence de la pente **30363** est une « Slope Brick 18 4×2 », avec **deux tenons apparents**. La référence **3003** est une brique **2×2** officielle ; la **3002** est une brique **2×3**. La géométrie LDraw 034 fournit la position réelle des deux tenons exposés dans chaque orientation. Source officielle : [30363](https://library.ldraw.org/parts/list?tableSearch=30363.dat), [3003](https://library.ldraw.org/parts/3486).

**RÈGLE CONSERVATRICE :** il ne suffit pas que quatre positions de tenons soient dans l'enveloppe de la brique centrale ; cela reste une **hypothèse de prise mécanique** sur sa sous-face, à confirmer physiquement. Le test LDraw des trois paires ne fait pas une simulation de la force de serrage.

## Vérifications automatiques

1. **Deux tenons exposés par pente**, basés sur la transformation LDraw *déjà vérifiée*, pas un bbox fabriqué.
2. **Aucune superposition** de tenons entre les deux pentes.
3. **Quatre tenons dans la sous-face projetée de la même brique**, au même niveau, dont deux de gauche et deux de droite.
4. Si la bibliothèque LDraw est fournie, **trois vérifications de paires** : pente gauche/droite et chaque pente/brique centrale. Rejet d'une collision **entre les corps de deux pentes indépendantes** dans ce nouveau montage. Les intersections brique/tenon peuvent être de la connexion volontaire et restent **physiquement non prouvées**.
5. Pas de recherche sans limite : deux écarts au maximum (0,1) × deux orientations (0,1), puis décision.

**FICHIERS EXPÉRIMENTAUX** : export `candidate-decisions.json`, puis, uniquement lorsqu'un cas passe les contrôles géométriques retenus, `essai-faitage-3-pieces-NOT-CERTIFIED.ldr` et `ESSAI-3-PIECES.md`. Si aucun cas ne passe : `AUCUN-MONTAGE-APPROUVE.txt`, pas de notice dangereusement affirmative.

## Test utilisateur — trois pièces, sans achat imposé

- Deux **30363** et, selon le choix informatique, une **3003** ou une **3002**.
- Essayer de prendre simultanément les **deux paires de tenons des pentes** dans le dessous de la **même brique de jonction**. Ne jamais forcer.
- Vérifier que la pièce relie réellement les **deux pans**, qu'on peut démonter et remonter sans déformation.
- Les pièces peuvent être tenues à la main pour ce premier test d'emboîtement ; **cela ne teste PAS la tenue d'une toiture sur des murs**.

La **preuve finale de ce jalon** devra être apportée par le véritable essai de montage de l'utilisateur, pas un rendu 3D.

## Limites et suite

Ce test **n'approuve pas** la sous-face des pentes sur l'ossature, ne fournit aucun chemin de charge à la maison, ne mesure pas les forces, ne génère aucune notice finale. Si aucun montage n'est constructible, changer de **famille de liaison LEGO documentée** plutôt que relancer les audits précédents du même capuchon 26603 et potelet 3005.

**GUIDED-004 : exactement 1 890 pièces, intact. PR #881, branche main inchangées. NOT_CERTIFIED.**
