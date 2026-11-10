# BOLDÜNGO — Mission 019 : précontrôle de la toiture B3

## Périmètre vérifié
- Branche : `feat/lego2-b1-guided004-full-house-experiment`
- HEAD du modèle au contrôle : `5e819d8c96a78e4d33c9ac0a284df99c6d0b7c13`
- Source unique : `missions/B3/generated/GUIDED004-B3-1904.ldr` (blob `288c60fde76918128d8b955f78ebfa9afc2dfe8e`).
- Fichier LDraw retrouvé et analysé au niveau des enregistrements de placement (`1 ... .dat`).
- **1 904** occurrences de pièces au total, dont **408** occurrences de `30363.dat` (toiture) et **1 496** autres références. Le contrôle rectangulaire des 1 496 pièces, évoqué en contexte, est un résultat antérieur non rejoué ici.
- Modèle architectural GUIDED-004 : ne pas confondre avec l'ancien benchmark à façade de 10 mètres ni avec le modèle visuel 019 (2 852 volumes).

## Campagne 019 — verdict rigoureux
| Information | Résultat |
| --- | --- |
| Pièces de toiture identifiées dans le vrai B3 | **408 / 408** |
| Pièces de toiture examinées avec maillages LDraw réels | **0 / 408** |
| Couples toiture–toiture ou toiture–murs testés physiquement | **0** |
| Collisions matérielles **confirmées** par maillage | **0 constatée, mais recherche NON EXÉCUTÉE** |
| Emboîtements physiquement compatibles **confirmés** | **0 constaté, mais recherche NON EXÉCUTÉE** |
| Contacts sans connexion démontrée | **NON DÉTERMINÉ** |
| Nombre d'interactions indéterminées | **NON DÉNOMBRABLE** sans géométries ; **408 pièces de toiture non contrôlées** |
| Statut | **BLOQUÉ — CONTRÔLE PHYSIQUE NON DÉMONTRÉ** |

**Ne pas lire les zéros ci-dessus comme « aucune collision » ou « aucune interaction » : aucun résultat géométrique valide n'a été produit.** Il est également incorrect de compter 408 « interactions indéterminées » : 408 désigne des *pièces*, pas des couples en interaction.

## Blocage précis
Le moteur existant `lego_geometry_engine` (`LDrawLibrary`, `candidate_pairs`, `check_collision`, `find_connections`) est présent dans le dépôt et a été inspecté. Sa bibliothèque de démonstration `lego_geometry_engine/tests/fixtures/ldraw/` ne contient pas `parts/30363.dat`, ni sa dépendance `parts/s/30363s01.dat` ou les primitives/subfiles requis. Elle ne contient que quelques références (notamment `parts/3005.dat`). Aucune bibliothèque LDraw complète n'est disponible sur le système d'exécution local ; l'accès réseau sortant local à `raw.githubusercontent.com` échoue à la résolution DNS. Le dépôt fournit bien `scripts/download_ldraw_probe_066.py` avec une source épinglée, mais il aurait fallu pouvoir télécharger et développer la fermeture de dépendances LDraw de toutes les familles voisines, ce qui n'a pas été réalisé.

Sans ces maillages :
1. impossible d'obtenir les véritables AABB des pièces inclinées `30363` pour le filtrage spatial 3D ;
2. impossible de calculer les intersections de triangles sur les paires candidates ;
3. impossible de distinguer collision matérielle, emboîtement, contact et cas indéterminé avec preuve.

Par précaution, la méthode `analyze_assembly` de cette révision classe certaines collisions de maillages avec connecteurs alignés comme contacts ; une future analyse ne devra **pas** assimiler une coïncidence nominale de connecteurs à une preuve suffisante qu'aucune matière solide ne s'interpénètre. Les tolérances, l'insertion et la stabilité ne sont pas certifiées.

## Intégrité
- Aucune pièce, aucune transformation LDraw, aucun fichier source de la maison modifié.
- Aucun faux scan AABB ni verdict tiré d'une approximation visuelle.
- Aucun workflow ni CI générale lancé.
- Une seule campagne de vérification documentaire et d'accès aux géométries ; arrêt dès le constat du blocage.
- Prochaine condition préalable *sans exécution ici* : mettre à disposition, pour le moteur existant, `30363.dat` et sa fermeture de dépendances ainsi que les géométries des pièces voisines.
