# LEGO2-076 — Potelet LEGO central 1×1 sous le faîtage

## Résultat ciblé

La mission 075 a identifié une impossibilité pour la **brique de tête 3002
(2×3)** : ses tenons occupaient quatre positions déjà utilisées par les
versants **30363**.

L'alternative reprend directement la colonne **BRICK_1X1 (3005)**
envisagée par 070, sans l'élargir. Pour le faîtage de largeur trois tenons,
la colonne occupe la ligne centrale entre les deux lignes de tenons exposés
des versants. Les trois groupes de tenons ne se superposent donc plus.

Dans le cas étudié, la connexion **mur existant → briques 1×1 empilées**
est nominalement `VALID` via `validate_connection` et la chaîne
de la mission 071 atteint la cote architecturale z=0. Ceci ne signifie
pas que la fondation soit certifiée.

## Le blocage restant : l'emboîtement à trois pièces

La tuile **26603 (2×3)** présente deux tubes sous sa face interne, et une
jupe périphérique. Les positions de ses deux tubes sont connues grâce
à la mission 073, mais rien n'établit un embrayage de la tuile sur
un **seul tenon central 1×1**, simultanément aux **quatre tenons
exposés des deux pentes 30363**.

Le déplacement des versants ou l'ajout d'une brique pleine largeur
réintroduirait des conflits : aucune modification de ce type n'est
effectuée. Le couvre-faîtage 2×4 de l'autre orientation utilise une
autre sous-face et reste également **UNKNOWN**.

La nouvelle vérification
`assess_central_ridge_post(model, library=None, max_sites=8,
max_mesh_pairs=60)` réutilise :
- l'ancrage réel, les chaînes de briques et les collisions
  potelet-versants/couvre-faîtage de **070/071** ;
- les véritables coordonnées de tenons **30363** documentées en 065/075 ;
- les paires LDraw de **066** pour la tuile face aux deux pentes
  et les pentes entre elles.

### Critères de décision

- **INVALID** uniquement si le potelet réclame un tenon déjà occupé par un
  versant, ou ne touche pas la bonne surface nominale de la tuile ;
- **REVIEW_REQUIRED** si les maillages présentent une intersection. Celle-ci
  peut représenter une interférence LEGO voulue et demande un expert ;
- **UNKNOWN** si un appui est absent, la géométrie indisponible, le budget
  épuisé, ou si la liaison simultanée des trois éléments n'est pas démontrée.

**Aucune solution d'emboîtement complet n'est déclarée VALID.** Les
maillages LDraw ne vérifient pas le serrage, la souplesse des matières,
le chemin réel d'assemblage ni la résistance à la charge.

Les essais sont limités à deux orientations, plusieurs dimensions de
maisons, ainsi que des cas sans support. Ils sont **non-mutants** :
GUIDED-004 garde ses **1 890 pièces**, sans mouvement de toiture, sans
changement de pente et sans suppression d'appui.

## Conclusion

Le potelet **1×1 élimine le conflit précis de quatre tenons** identifié
pour la 3002. Il ne résout **pas** à lui seul la connexion
potelet–tuile–deux versants. Aucun nouveau montage n'est autorisé.

**Statut : NOT_CERTIFIED.**
