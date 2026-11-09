# BOLDÜNGO — Mission 025 : vérification matérielle du faîtage

## Objet
Une seule paire réelle du B3, sans modification : `roof-000185` (`30363.dat`, 830,-960,20) contre `roof-000392` (`30363.dat`, 790,-960,20), orientations opposées. Quatre témoins de triangles croisés démontrés en M024, dont les indices 0/601, 0/698, 1/601 et 2/601.

## Statut initial : C — INDÉTERMINÉ
Le job M025 ciblé est configuré pour reproduire ces quatre témoins, remonter jusqu'aux lignes et primitives de `30363.dat` et `s/30363s01.dat`, puis appliquer sans modification `inspect_solid_shell` et `inspect_shared_interior` du moteur existant `ridge_material_volume_080.py`.

La preuve attendue se trouvera dans les artefacts du job ciblé : `DIAGNOSTIC-FAITAGE-M025.md` et `PREUVES-FAITAGE-M025.json`. **Ne pas déclarer l'analyse exécutée avant la fin de GitHub Actions.**

## Limites
- Quatre croisements de triangles de maillages ne prouvent pas à eux seuls que deux corps rigides occupent le même volume incompatible.
- Les maillages LDraw peuvent être ouverts, mal orientés ou contenir des primitives de tenon/logement ; le test d'occupation exige un maillage fermé orienté et fiable.
- Une géométrie répétée n'est pas un certificat d'emboîtement LEGO.
- Constructibilité, stabilité, trajet d'insertion et propriétés matérielles **NON CERTIFIÉS**.
