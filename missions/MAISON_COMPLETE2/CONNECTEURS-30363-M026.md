# BOLDÜNGO — Mission 026 : preuve des connecteurs limités de 30363

## Source vérifiée
Révision LDraw épinglée : `pybricks/ldraw@c43ed06a128a10ed65675166bf42eb6fd608b9b0`.
- `parts/30363.dat:16` inclut sans rotation `s/30363s01.dat`.
- `parts/s/30363s01.dat:61–62` place explicitement deux `stud.dat` aux coordonnées locales **(−10,0,0)** et **(+10,0,0)** LDU, avec un axe vertical conservé.
- `p/stud.dat` décrit le tenon cylindrique LEGO authentique. Ces **deux tenons sont démontrés par provenance**, et **non déduits d'une boîte englobante**.
- `parts/s/30363s01.dat:18,34–37` décrit des primitives de tubes sous la pente, notamment `stud4a.dat` et `stud4s.dat` ; mais leur géométrie, leur hauteur variable et les autres évidements **ne suffisent pas à attribuer un plan de réception `anti_stud` sûr et universel**. Aucun connecteur inférieur n'est donc ajouté.
- `parts/s/3004s01.dat:15` contient `stud3.dat` (tube intérieur) et `:17,22` décrit les parois/évidements. La brique 3004 possède déjà les points `anti_stud` standards reconnus par le moteur aux coordonnées locales (±10,24,0).

## Petit assemblage indépendant — garde-fou
- Pente réelle 30363, placement identité. Brique réelle 3004, origine (0,−24,0) LDU : **deux alignements nominaux CONFIRMÉS en GitHub Actions** entre les tenons documentés de la pente et les réceptions nominales de la 3004, **placée au-dessus de la pente**. Attention : ce n'est PAS une jonction porteuse démontrée sous la pente.
- Position incorrecte 3004 (10,−24,0) : **aucun alignement de connexion** nominal attendu.
- Politique de collision : pour toute paire avec `30363.dat`, une réponse `COLLISION` du moteur **reste un signal de collision** même si deux connecteurs sont alignés. Aucune approbation automatique de matière rigide commune.
- Les autres familles de briques conservent la logique existante et les tests historiques.

## Résultats réels de la campagne ciblée — SUCCESS

- [GitHub Actions n°42710466686](https://github.com/ludodulac/boldungo/actions/runs/42710466686) : **19 tests PASS en 0,20 s**, un seul job ciblé ; **23 fichiers** de géométrie LDraw épinglée téléchargés dans le runner.
- **TEST A PASS :** 2 tenons supérieurs `30363` explicitement présents, 2 alignements nominaux avec `3004` à (0,−24,0).
- **TEST B PASS :** `3004` décalée à (10,−24,0) : zéro alignement reconnu.
- **TEST C PASS :** injection de l'état `COLLISION` du moteur pour la paire de vrais objets chargés : même avec 2 connecteurs alignés, l'assemblage reste **refusé** (`slope_30363_mesh_intersection_review_required`). Cela teste un garde-fou logiciel, **pas** la présence physique d'une telle collision.
- **TEST D PASS :** anciens connecteurs `3004` et `3005` conservés ; tests historiques du moteur PASS.
- **TEST E PASS :** bibliothèque d'imitation sans les deux références de tenon explicites : aucun connecteur `30363` inféré.
- **Conclusion limitée :** reconnaissance **nominale et justifiée** des tenons supérieurs ; dessous de la pente **INCONNU**. Aucun raccord physique porteur, insertion ou stabilité validé. Aucune pièce B3 déplacée.
- Artefact : `BOLDUNGO-M026-30363-TOP-STUD-TESTS-NOT-CERTIFIED` sur l'exécution ci-dessus.

## Statut et réserves
- Le code contient une extension ciblée de la bibliothèque existante : seuls les **deux tenons supérieurs expressément tracés** sont ajoutés, si et seulement si la bibliothèque LDraw contient les lignes canoniques sources. Les autres zones restent inconnues.
- Le résultat nominal d'alignement ne certifie ni un logement fabriqué exact, ni la trajectoire d'insertion, ni les tolérances du plastique, ni la stabilité de la maison. Une intersection signalée par le moteur reste à examiner.
- Le rapport de tests est disponible dans l'artefact du job M026 ; seuls les résultats ci-dessus, confirmés par ses journaux, sont qualifiés PASS.
- Modèle B3 et toutes les photographies : inchangés. PR #931 DRAFT, PR #941 intacte.
