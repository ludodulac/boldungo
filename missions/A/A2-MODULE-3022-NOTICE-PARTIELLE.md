# 🧱 A-2 — ORDRE DE MONTAGE DU MICRO-MODULE (NON CERTIFIÉ)

**Fichier LDraw :** `A2-MODULE-3022-PROPOSE.ldr` (24 véritables références).
**Emprise :** extrait intérieur de largeur 20 tenons de A1, bande Y=2..3 ; deux versants, deux rangées par versant.

Les `3003` sont des briques LEGO 2×2 ; les `30363` sont les briques inclinées 18°, 4×2 ; le faîtage est une plaque 2×2 `3022`.

1. Placer la baseplate `3811`. **Contact exact avec ses tenons non passé dans l'audit maillage complet** ; ne pas la supposer mécaniquement certifiée.
2. Monter à la verticale les piliers `left-j1-pier-z0…z6`, `right-j1-pier-z0…z6`, `left-j2-pier-z0…z9`, `right-j2-pier-z0…z9`. Poser chaque 3003 sur le précédent par axe vertical ; respecter d'abord les niveaux bas.
3. Ajouter les quatre briques 3003 de tête : `left-j1-bearing`, `right-j1-bearing`, `left-j2-bearing`, `right-j2-bearing`.
4. Insérer du haut vers le bas les premiers `30363` de chaque pan : `left-j1-30363`, `right-j1-30363`. Les dessous sont à la hauteur des tenons des 3003 porteurs.
5. Insérer de même les deux pièces du rang intérieur `left-j2-30363`, `right-j2-30363`. Elles possèdent des supports 3003 indépendants ; **ne pas prétendre à une liaison 30363→30363 par simples empreintes nominales**.
6. Poser la plaque **3022 2×2** sur les **quatre tenons** des deux éléments supérieurs, deux de chaque côté du faîtage.

Les pièces, orientations et coordonnées sont exportées par `scripts/construct_small_roof_a2.py`. Chaque pièce figure dans le `ORDER.json` généré en CI (24 entrées). Direction proposée : verticale depuis le dessus, monde LDraw `+Y` vers position finale (la montée physique est le vecteur `-Y`). **Ne pas prétendre à une insertion continue démontrée** : les mouvements n'ont été vérifiés qu'aux déplacements 48,32,24,16,8,4,2,0 LDU et les emboîtements finaux stud/tube ne sont pas prouvés exhaustivement.

**ARRÊT de validation :** la plaque `3022` a éliminé les deux `COLLISION` de maillage du candidat `3023b` dans le micro-module. Ce n'est ni une notice N5 entièrement certifiée, ni une preuve de rigidité N6. Ne pas répercuter ce montage à A1 complète avant d'établir les preuves manquantes.
