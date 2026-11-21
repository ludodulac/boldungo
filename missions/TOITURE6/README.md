# BOLDÜNGO — TOITURE-6 — fondation locale et deuxième mur (PR #941)

- **Acquis inchangés** : 43 pièces de TOITURE-5, dont 5 pièces de toiture
  LEGO 30363 et le chemin de connexion vers `wall-000707` puis
  `wall-000009`. Aucun réaudit du résultat TOITURE-5.
- **Nouvelle fondation expérimentale locale** : vraie baseplate LEGO
  `3811.dat` à (960,0,760), sous les deux pieds muraux B-3,
  `wall-000009` et `wall-000021`. Ce n'est **PAS** une fondation
  complète de la maison ni un ancrage au terrain.
- **Second mur original** : 31 pièces B3, depuis `wall-000021`
  jusqu'à `wall-000719`, 30 joints nouveaux contrôlés par LDraw.
- **Second chemin** : quatre briques officielles `3006.dat` avec
  liaison progressive à `TOITURE3-VARIANT-3006-ROW336-340`. Chaque
  maillage, connecteur, collision et insertion est testé.
- **Sixième pente candidate** : `roof-000315`, vraie LEGO `30363`
  de B-3, conservée à sa position source. Il s'agit d'une **hypothèse
  non certifiée** tant que les tests d'assemblage avec les cinq pentes
  déjà validées n'ont pas réussi. Ne pas additionner automatiquement
  aux cinq acquises.

`MODULE-VARIANTE.ldr`, `VIEWER-80.json`, `FONDATION.json`,
`DEUXIEME-APPUI.json`, `COLLISIONS.json`, `INSERTION.json`,
`BOM.json`, `PROVENANCE.json`, `RESULTAT.json` documentent
la nouvelle structure. La visionneuse reste celle de BOLDÜNGO :
`frontend/viewer.html?bundle=../missions/TOITURE6/VIEWER-80.json`.

**Bornes de la démonstration** : les deux chemins structurels utilisent
**deux colonnes murales différentes mais la même baseplate locale**.
Cela ne prouve ni indépendance des ancrages, ni tenue mécanique,
ni stabilité réelle ou flexion. La représentation 3D est un proxy
visuel ; les vérifications font appel aux véritables maillages LDraw.
Ne jamais confondre 80 éléments représentés et 80 éléments
géométriquement certifiés si les rapports n'établissent pas ce statut.

Aucune fusion ou publication, aucun changement B-3, 356, 019 ou viewer.
