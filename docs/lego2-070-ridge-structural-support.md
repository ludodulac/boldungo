# LEGO2-070 — Potelet de soutien sous faîtage (étude, non certifiée)

## Solution structurelle ciblée

Au lieu de déplacer une rangée de toiture, rechercher un **potelet vertical**
sur une colonne de tenons déjà portée par une maçonnerie existante. Au-dessus
de ce potelet, étudier la couverture transversale du faîtage déjà proposée
par le planificateur 065. Les deux versants et leurs appuis d'origine restent
à leur position initiale.

1. Réutiliser les coordonnées des vrais tenons supérieurs de la pente 30363.
2. N'autoriser le potelet que dans une **colonne intérieure** d'une tuile de
   faîtage transversale existant au catalogue LEGO.
3. Trouver un support (mur ou support de toit) **réel**, strictement sous la
   tuile à la même coordonnée XY. Aucun support flottant n'est inventé.
4. Proposer un empilement de vraies `BRICK_1X1` (3005 LDraw), uniquement si
   la hauteur peut être obtenue par briques entières de trois plaques.
5. Utiliser `validate_connection()` pour les interfaces potelet-maçonnerie et
   potelet-potelet ; refuser tout raccord non documenté.
6. Détecter la maçonnerie déjà présente sur le trajet, sans la déplacer.
7. Vérifier avec `_pair()` (géométries LDraw) les intersections des potelets
   avec les éléments de toit proches si la bibliothèque est disponible.

La proposition est **un potelet local sous couverture**, pas encore une
poutre de faîtage continue, ni un système de fermes certifié. Des potelets
isolés ne prouvent pas la reprise des charges sur la longueur de la toiture.

## Vérifications qui restent ouvertes

- Jonction du potelet à la face inférieure de la tuile : **UNKNOWN**.
- Emboîtement de la tuile sur les deux versants : **UNKNOWN**.
- Collision préexistante entre versants (066–069) : **non résolue**.
- Trajet complet des charges vers le sol, flexion, flambement des potelets,
  stabilité, assemblage et insertion réelle : **UNKNOWN**.
- Les exclusions par empreinte nominale ne remplacent pas une vérification
  3D exhaustive de la totalité de la maison.

**Règle** : ni une projection de tenons, ni un statut `VALID` sur une
interface locale, ni l'absence de collision ponctuelle ne permettent
`CERTIFIED`. Toutes les propositions restent `NOT_CERTIFIED`.

## Réutilisation et tests

API : `assess_structural_ridge_posts(model, library=None, max_sites=8)`,
dans `backend/brickhouse/bricks/ridge_structural_posts_070.py`.

Tests : `tests/bricks/test_ridge_structural_posts_070.py`, incluant deux
orientations de toiture, absence de point d'appui, éléments existants gênants,
raccord non documenté, plafonds de tests, modèle canonique si son export est
disponible, et son maintien inchangé.

**Aucune écriture** sur GUIDED-004, LEGO2 ni `main` par ce planificateur.
