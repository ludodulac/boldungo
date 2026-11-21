# LEGO2 060C — Géométrie ≠ preuve de connexion

Deux contrôles publics **explicitement distincts** réutilisent le même
catalogue orthogonal, les dimensions/rotations, la grille et la détection des
collisions solides. Aucun ne certifie la résistance, la stabilité, la
possibilité d'insertion ou la constructibilité réelle.

## A. Géométrie seulement — `GEOMETRY_ONLY`

- `GeometricPlacementGate`, `build_geometrically(parts)` et
  `verify_geometrically_connected(parts)` dans `physical_placement_gate.py`.
- `generate_geometrically_screened_assembly_plan(model)` dans
  `physical_assembly.py` vérifie aussi l'ordre de notice par rejeu.
- Valide le contact vertical nominal par chevauchement de colonnes de tenons.
  Ce contact **ne constitue pas** une liaison LEGO vérifiée.
- `connector_validation = NOT_CHECKED`, `physical_certification = False`.
  Un succès ne peut pas être exporté comme `VALID` physique.
- Les anciens démonstrateurs de murs, d'ouverture et leur préflight/export
  empruntent **explicitement** ce chemin. Le préflight renvoie
  `validation_level: GEOMETRY_ONLY`,
  `connector_validation: NOT_CHECKED`,
  `physical_evidence: NOT_CERTIFIED`.

## B. Connecteurs stricts — `CONNECTOR_EVIDENCE_STRICT`

- `PhysicalPlacementGate`, `build(parts)` et `verify_connected(parts)`.
- `generate_physically_screened_assembly_plan(model)` reste strict.
- Réutilise `connectors.validate_connection` **sans modifier les familles** :
  seul `VALID` peut justifier un support et une arête de connectivité.
  `UNKNOWN` et `INVALID` sont refusés, avec motifs distincts.
- `physical_certification = False` même ici : `VALID` est une preuve
  d'interface nominale dans le périmètre étudié, non de clutch/stabilité.

## Choix du contrôle

Utiliser A pour les préflights **géométriques** de démonstrateurs dont les
connecteurs n'ont pas été étudiés et pour tester leur ordre de montage nominal.
Utiliser B pour toute revendication de support sur des interfaces documentées.
Ne jamais faire passer un résultat A pour une certification B.

La maison GUIDED-004 (1890 pièces), les variantes 059M/059N (1894 pièces),
la notice de 317 étapes et `NOT_CERTIFIED` restent hors de cette mission.
