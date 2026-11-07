# TOITURE-7 — aucun faux deuxième appui

PR #941 DRAFT. Départ : modèle **75 pièces RETENUES** de TOITURE-6
copié en tant qu'objet Git, SHA inchangé : `MODULE-RETENU.ldr`
et `VIEWER-RETENU.json`.

## Deux tests géométriques limités

1. L'interface originale B-3 `roof-000223` (30363) et
   `wall-000719` (3008), tous deux immobiles : cavités, tenons,
   contact des vrais triangles LDraw et insertion continue.
2. Seulement **deux alternatives expérimentales**, jamais ajoutées
   sans preuve complète : six briques officielles `3001.dat` (2×4)
   réparties sous les rangées inclinées, variante A centrale Z=620,
   variante B au bord Z=700. Le support commun des cinq vraies
   pentes à X=960 reste intact. Aucun réemploi du tracé des quatre
   longues 3006 de TOITURE-6.

Les seuls statuts fiables sont ceux enregistrés à l'issue du test ciblé
dans `ROOF223-WALL719.json`, `DEUX-CHEMINS.json`,
`COLLISIONS.json`, `INSERTION.json` et `RESULTAT.json`.
Un contact du toit 223 avec le mur 719 **ne prouve pas** que ce
toit touche les cinq pentes déjà retenues.

Visualisation mobile **de la bonne version 75** (non de la version
80 en échec), par la visionneuse BOLDÜNGO existante :
`frontend/viewer.html?bundle=../missions/TOITURE7/VIEWER-RETENU.json`.
Capture si test navigateur réussi : `toiture7-retained-mobile.png`.

L'unique baseplate 3811 est une fondation LEGO **locale**, pas un
ancrage au sol ou une fondation de la maison entière. La flexion,
les forces d'emboîtement, le flambement et la stabilité réelle
restent NON DÉMONTRÉS.

Aucune fusion, aucun déploiement, aucun changement du modèle B-3,
de MAISON-4, de 019, de TOITURE-1…6, ni de la visionneuse.
