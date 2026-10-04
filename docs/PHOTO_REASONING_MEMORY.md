# Mémoire de raisonnement photographique Boldüngo

## Statut

Ce document est une mémoire évolutive des principes génériques appris pendant le développement de Boldüngo.

Il ne contient pas la vérité d'un benchmark particulier et ne doit jamais servir à injecter dans un candidat des informations privées propres à une maison. Il conserve les règles de raisonnement réutilisables qui devront guider les futurs prompts, contrats et moteurs d'analyse photographique.

## 1. Hiérarchie de compréhension

Boldüngo ne doit pas réduire l'analyse à « visible / inconnu ».

Pour chaque fait architectural, distinguer :

1. **OBSERVÉ** — directement visible dans une ou plusieurs photos.
2. **DÉDUIT MULTIVUE** — établi par recoupement de plusieurs vues, identités, orientations ou continuités.
3. **DÉDUIT ARCHITECTURALEMENT** — conséquence fonctionnelle ou physique raisonnable des éléments observés, sans métrique inventée.
4. **HYPOTHÈSE** — explication plausible mais non suffisamment établie.
5. **À CONFIRMER** — incertitude importante qu'une question simple à l'utilisateur peut résoudre.
6. **INCONNU** — information qui ne peut honnêtement pas être déterminée avec les éléments disponibles.
7. **CONTRADICTOIRE** — éléments de preuve incompatibles à conserver explicitement jusqu'à résolution.

Une information non directement visible n'est donc pas automatiquement UNKNOWN.

## 2. Déduction architecturale

Le moteur doit se poser des questions fonctionnelles et spatiales, notamment :

- Par où une personne peut-elle circuler ?
- Quels éléments doivent physiquement se rejoindre pour que l'accès observé fonctionne ?
- Une surface visible est-elle un palier, une terrasse, un seuil ou un simple volume ?
- Une ouverture est-elle réellement praticable ou seulement vitrée ?
- Un escalier visible doit-il nécessairement rejoindre une circulation supérieure ?
- Deux éléments vus depuis des angles différents sont-ils le même objet ?
- Un objet visible en arrière-plan appartient-il réellement au bâtiment cible ?

Une continuité fonctionnelle peut être déduite alors que sa géométrie métrique reste inconnue.

Exemple générique : si un escalier constitue le seul accès extérieur visible à une circulation supérieure et que cette circulation dessert des ouvertures du bâtiment, le moteur doit rechercher et peut proposer une continuité escalier → palier → terrasse. Il ne doit pas inventer pour autant les dimensions, le nombre de marches ou la géométrie cachée de la jonction.

## 3. Raisonnement multivue

Avant de métriser :

- inventorier les observations locales de chaque photo ;
- identifier les objets candidats répétés entre vues ;
- utiliser coins, pignons, ouvertures, cheminées, antennes, terrasses, escaliers et autres repères pour établir les correspondances ;
- distinguer objet du bâtiment cible et objet d'un bâtiment voisin ;
- rechercher les continuités et incompatibilités ;
- conserver les occlusions ;
- réexaminer les hypothèses après chaque correspondance multivue.

La présence d'un objet dans une image ne prouve pas son appartenance au bâtiment cible. Son déplacement relatif entre plusieurs vues peut permettre de résoudre cette appartenance.

## 4. Géométrie qualitative avant métrique

Boldüngo doit pouvoir reconstruire une forme générale sans prétendre connaître des mesures exactes.

Exemples :

- un pignon visible peut établir une toiture à deux pans sans fournir un angle numérique exact ;
- la pente visuelle d'un pignon peut fournir une proportion de reconstruction sans être présentée comme une mesure ;
- un escalier peut être reconnu comme droit, tournant ou en L sans connaître son nombre exact de marches ;
- une terrasse peut avoir une étendue approximative suffisante pour une miniature alors que ses dimensions réelles restent inconnues ;
- l'existence de supports peut être certaine tandis que leur nombre exhaustif et leurs coordonnées restent inconnus.

## 5. Questions utilisateur ciblées

Le premier passage ne doit pas chercher à tout résoudre.

Lorsqu'une incertitude est importante pour la reconnaissance ou la construction et qu'elle peut être résolue simplement, Boldüngo doit poser une question ciblée après sa première analyse.

Exemples :

- « Cette cheminée appartient-elle à votre maison ou au bâtiment derrière ? »
- « L'escalier tourne-t-il derrière ce mur ? »
- « Ces deux surfaces de terrasse communiquent-elles directement ? »
- « Cette grande ouverture est-elle une porte, une porte-fenêtre ou une fenêtre ? »
- « Pouvez-vous indiquer approximativement la largeur de cette façade ? »

Ne pas demander à l'utilisateur des informations qui n'ont pas d'impact perceptuel ou constructif significatif.

## 6. Fidélité perceptuelle LEGO

L'objectif n'est pas une reproduction métrique servile de chaque détail réel.

La miniature doit prioritairement conserver ce qui fait reconnaître la maison :

- silhouette et proportions générales ;
- volumes et niveaux ;
- forme et présence de la toiture ;
- ouvertures principales et leurs proportions ;
- accès et circulations extérieures ;
- terrasse, palier et escalier ;
- cheminée et autres éléments distinctifs ;
- garde-corps ;
- couleurs et changements de traitement de façade ;
- encadrements de fenêtres ;
- volets ou éléments caractéristiques lorsqu'ils sont perceptuellement importants.

Le nombre exact de planches, marches, poteaux ou petites pièces peut être simplifié si la structure reste architecturale, reconnaissable et constructible.

## 7. Matériaux et apparence

Distinguer :

- matériau observé avec confiance ;
- matériau probable ;
- matériau inconnu.

Une incertitude de matériau ne doit pas empêcher la reconstruction d'une géométrie bien établie.

Lorsqu'un matériau influence fortement l'apparence et reste ambigu, utiliser une représentation générique honnête ou demander confirmation.

## 8. Ouvertures

Ne pas traiter toutes les ouvertures comme équivalentes.

Chercher à distinguer, lorsque les pixels le permettent :

- fenêtre ;
- porte ;
- porte-fenêtre ;
- baie double ;
- briques de verre ;
- ouverture technique ;
- coffret ou équipement qui n'est pas une ouverture architecturale.

La profondeur métrique d'une baie peut rester inconnue même lorsque son existence, son type et sa position qualitative sont établis.

## 9. Structure visible

Les éléments structurels qualitatifs doivent être conservés même sans métriques complètes.

Exemple : sous une terrasse, un poteau vertical visible établit l'existence de support vertical, pas son inventaire exhaustif.

Un **contreventement** est une pièce diagonale reliant la structure afin de la stabiliser latéralement. Son existence peut être importante pour la silhouette constructive sans nécessiter de reproduire exactement chaque diagonale.

## 10. Séparer vérité architecturale et choix LEGO

La compréhension de la maison et son adaptation LEGO sont deux niveaux différents.

Architecture :
« il existe une terrasse bois surélevée avec supports ».

LEGO :
« la miniature utilisera N éléments pour évoquer cette structure ».

Le second ne doit pas rétroactivement falsifier le premier.

Un choix discret LEGO — par exemple une profondeur d'un tenon pour rendre une baie lisible — est une convention de représentation tant qu'aucune mesure réelle ne l'établit.

## 11. Leçons des prototypes #723 et #728

- #723 : améliorer l'appui constructif et le linteau d'une ouverture améliore surtout la cohérence constructive ; l'effet visuel peut rester faible.
- #728 : une véritable profondeur tridimensionnelle de baie peut produire un gain visuel architectural important.
- Ces prototypes établissent des principes génériques, pas des métriques universelles.
- Ne jamais conclure que toutes les baies réelles ont une profondeur d'un tenon.

## 12. Règle de mise à jour de cette mémoire

Après chaque benchmark, contrôle humain ou expérience qui révèle une règle générique :

1. formuler la leçon indépendamment du bâtiment particulier ;
2. distinguer observation, déduction et convention de représentation ;
3. ajouter la règle ici seulement si elle est réutilisable ;
4. ne jamais transformer une vérité privée de benchmark en règle universelle ;
5. faire évoluer ensuite les prompts et contrats génériques à partir de cette mémoire de manière explicite et testable.

Cette mémoire est destinée à empêcher la perte des apprentissages entre conversations et itérations du projet.
