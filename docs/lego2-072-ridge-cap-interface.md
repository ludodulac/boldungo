# LEGO2-072 — Interface potelet / pièce de faîtage

## Étude ciblée, sans changement de la maison

Le potelet LEGO 1×1 des missions 070 et 071 peut fournir un **appui
nominal** à une brique LEGO 2×3 (3002). L'interface entre le tenon supérieur
de la brique 1×1 et la cavité inférieure de 3002 est déjà reconnue
`VALID` par le contrôle conservateur des connecteurs du projet.

Pour les seuls couvre-faîtages `TILE_2X3` (26603), la proposition 072
**remplace seulement la dernière 1×1 expérimentale** par une
`BRICK_2X3`, exactement sous la couverture, dans son orientation et son
empreinte d'origine. Ce n'est pas une construction appliquée au modèle.
Il faut au moins une autre 1×1 en dessous, avec une chaîne de mur existante
et documentée jusqu'à z=0 (contrôle 071).

La pente, les versants, les supports et les 1 890 pièces canoniques de
GUIDED-004 sont inchangés.

## Preuves établies / limites

1. **Potelet 1×1 -> brique de tête 2×3** : connexion verticale nominale
   `VALID` dans le domaine précisément documenté du contrôleur existant.
2. **Brique de tête 2×3 -> tuile de faîtage 26603** : `UNKNOWN`.
   Les tenons qui se projettent dans la même maille ne prouvent pas
   l'embrayage de la sous-face 26603.
3. **Tuile -> deux versants 30363** : `UNKNOWN`. Les intersections
   existantes entre versants ne sont ni supprimées ni déclarées résolues.
4. **Interférences 3D** : l'étude réutilise `_pair()` et les vrais
   maillages LDraw sur la brique de tête, la tuile projetée et les
   parties connues proches. Une collision est marquée
   `MESH_INTERSECTION_REVIEW_REQUIRED`. Des fichiers de géométrie absents
   restent `UNKNOWN` : absence de preuve ne signifie jamais absence
   de collision.
5. **Stabilité de l'assemblage** : résistance à la flexion, torsion,
   flambement, fondations, pièces non analysées et ordre d'insertion
   non vérifiés. Un seul tenon inférieur ne garantit pas un contreventement
   de la brique 2×3.

Les formes et les orientations différentes sont couvertes par les tests.
Le couvre-faîtage `TILE_2X4` et les toits à d'autres géométries ne
bénéficient d'aucune généralisation automatique. Ils restent inconnus.

## API et protocole de revue

`assess_ridge_cap_adapters(model, library=None, max_sites=8,
max_mesh_pairs=80)`, dans
`backend/brickhouse/bricks/ridge_cap_adapter_072.py`.

Ce planificateur conserve `model_mutated=False` et
`physical_certification=NOT_CERTIFIED` même lorsqu'une connexion
nominale locale est `VALID`. La présence de fichiers officiels LDraw
ne garantit ni l'emboîtement mécanique ni la constructibilité.

**Aucun déplacement ni ajout de pièce n'est approuvé dans GUIDED-004.**
