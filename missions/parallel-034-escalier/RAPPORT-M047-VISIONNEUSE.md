# BOLDÜNGO — M047 · Prototype limité de formes LEGO visibles
- HEAD de départ : `9a51b740d7d48f16485c6c1e37d7b74380573160`, PR #945 maintenue DRAFT.
- **Couche réellement identifiée** : `frontend/viewer.js::makePartMesh()`; le corps était `THREE.BoxGeometry` et les tenons `CylinderGeometry` étaient désactivés au-delà de 1 200 pièces et sur de nombreux mobiles.
- **Changement** : dans le visualiseur public `viewer.html`, option cochée par défaut « Détails LEGO (zone ciblée) ». Elle sélectionne des briques/plaques standards de surface maximum 8 tenons, prioritairement proches de la première ouverture, ou à défaut sur la façade avant.
- Uniquement ces pièces reçoivent un `RoundedBoxGeometry` à arêtes légèrement adoucies et des **tenons cylindriques instanciés** (positions LEGO nominales, 0,6 tenon de diamètre et 0,15 de hauteur). Toutes les autres pièces conservent exactement la même méthode qu'avant. Les vitrages `window_pane` ne sont pas déguisés en briques de verre.
- Budget limité à **48 briques sur téléphone, 144 sur grand écran** indépendamment de la taille de l'export. `InstancedMesh` permet un tirage des tenons par brique ; ce n'est pas une estimation de FPS. Affichage désactivable sans perdre le chargement JSON.
- Inertie du contrôle `OrbitControls` désactivée (`enableDamping=false`).
- **Ce n'est pas un maillage officiel LDraw** : la sous-face, les logements tubulaires, la géométrie exacte des ouvertures et les autres briques ne sont pas encore modélisés. Les surfaces restent des approximations de visualisation, sans prétention de connexions mécaniques.
- **Tests ciblés** : 15 contrôles unitaires et statiques, sélection locale, taille de budget, rotation, tenons, opt-out, chargement existant, contrôle inertie. Pas de test navigateur réel ni de mesure de FPS exécutés.
- Fichiers modifiés/créés : `frontend/viewer.js`, `frontend/viewer.html`, `frontend/viewer-lego-detail-047.mjs`, `tests/frontend/test_viewer_lego_detail_047.mjs`.
