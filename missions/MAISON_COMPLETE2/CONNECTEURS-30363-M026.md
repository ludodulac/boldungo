# BOLDÜNGO — Mission 026 : preuve des connecteurs limités de 30363

## Source vérifiée
Révision LDraw épinglée : `pybricks/ldraw@c43ed06a128a10ed65675166bf42eb6fd608b9b0`.
- `parts/30363.dat:16` inclut sans rotation `s/30363s01.dat`.
- `parts/s/30363s01.dat:61–62` place explicitement deux `stud.dat` aux coordonnées locales **(−10,0,0)** et **(+10,0,0)** LDU, avec un axe vertical conservé.
- `p/stud.dat` décrit le tenon cylindrique LEGO authentique. Ces **deux tenons sont démontrés par provenance**, et **non déduits d'une boîte englobante**.
- `parts/s/30363s01.dat:18,34–37` décrit des primitives de tubes sous la pente, notamment `stud4a.dat` et `stud4s.dat` ; mais leur géométrie, leur hauteur variable et les autres évidements **ne suffisent pas à attribuer un plan de réception `anti_stud` sûr et universel**. Aucun connecteur inférieur n'est donc ajouté.
- `parts/s/3004s01.dat:15` contient `stud3.dat` (tube intérieur) et `:17,22` décrit les parois/évidements. La brique 3004 possède déjà les points `anti_stud` standards reconnus par le moteur aux coordonnées locales (±10,24,0).

## Petit assemblage indépendant — garde-fou
- Pente réelle 30363, placement identité. Brique réelle 3004, origine (0,−24,0) LDU : **deux alignements nominaux** entre les tenons documentés de la pente et les réceptions nominales du support, à confirmer par l'unique campagne GitHub Actions.
- Position incorrecte 3004 (10,−24,0) : **aucun alignement de connexion** nominal attendu.
- Politique de collision : pour toute paire avec `30363.dat`, une réponse `COLLISION` du moteur **reste un signal de collision** même si deux connecteurs sont alignés. Aucune approbation automatique de matière rigide commune.
- Les autres familles de briques conservent la logique existante et les tests historiques.

## Statut et réserves
- Le code contient une extension ciblée de la bibliothèque existante : seuls les **deux tenons supérieurs expressément tracés** sont ajoutés, si et seulement si la bibliothèque LDraw contient les lignes canoniques sources. Les autres zones restent inconnues.
- Le résultat nominal d'alignement ne certifie ni un logement fabriqué exact, ni la trajectoire d'insertion, ni les tolérances du plastique, ni la stabilité de la maison. Une intersection signalée par le moteur reste à examiner.
- Le rapport définitif des tests est dans l'artefact du job M026 ; aucune affirmation PASS avant consultation des journaux.
- Modèle B3 et toutes les photographies : inchangés. PR #931 DRAFT, PR #941 intacte.
