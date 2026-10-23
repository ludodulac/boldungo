# BOLDÜNGO — Mission 097 : vraie orientation LDraw et assemblage limité

## Décision technique — 23 octobre 2026

**NE PAS FUSIONNER COMME STRUCTURE PORTEUSE.** L'essai 097 possède
des trous nominalement coaxiaux et de vraies pièces LDraw, mais un coude
Technic articulé peut pivoter et s'écraser sous compression. Un chemin
de graphe N2 n'est pas un chemin porteur N4.

## Défaut de conception découvert dans la famille 095

Les coordonnées des trous 32278 et 32524 étaient calculées correctement
sur leur longueur, mais la rotation LDraw historique des poutres utilisait
leur axe LOCAL X comme axe de trou. **Les primitives LDraw des trous traversants
sont orientées sur LOCAL Y.** Une broche déclarée coaxiale en XYZ ne traversait
donc pas le vrai corps représenté de la poutre.

La broche Technic **2780.dat** est assemblée depuis `confric5.dat` et son
axe principal de pièce est LOCAL Z ; **6558.dat** suit aussi l'axe LOCAL Z.
La rotation historique `PIN_MATRIX` envoyait cet axe dans WORLD -Y,
alors que le calcul prétendait WORLD Z. Double faux positif N2.

La variante 097 seule corrige automatiquement les matrices locales des
vraies poutres 095 (32278/32524) et des broches 2780/6558, en
laissant les axes de longueur, coordonnées des centres de trous,
angles, dimensions architecturales, façades, anciens modèles et canonique
de 1 890 pièces inchangés. La correction des axes n'est PAS un balayage
de maillage ni une nouvelle validation de tenue mécanique.

Références primaires :
- [LDraw 32278.dat — Technic Beam 15](https://library.ldraw.org/parts/5679)
- [LDraw 32524.dat — Technic Beam 7](https://library.ldraw.org/parts/list?tableSearch=32524.dat)
- [LDraw 32017.dat — Technic Beam 5 × 0,5](https://library.ldraw.org/parts/5505)
- [LDraw 2780.dat — Technic Pin](https://library.ldraw.org/parts/3099)
- [LDraw 6558.dat — Technic Pin Long](https://library.ldraw.org/parts/list?tableSearch=6558.dat)
- [LDraw primitives — orientation des perçages Technic](https://wiki.ldraw.org/wiki/Primitives_Reference)

## Alternative réellement construite

Au lieu de supposer 0,0507923 LDU de tolérance fabricante,
la nouvelle travée 0 remplace un renfort 32524 + 2 broches par :
**2×32017 (5 trous, épaisseur 10 LDU), 3×2780 (2L)**.
Une des 3700 de toiture est conservée.
Les deux liens font exactement 80 LDU entre leurs trous extrêmes.
L'emplacement de la charnière du milieu est trouvé par l'intersection
de deux cercles ; trois axes de broches coïncident mathématiquement.
Les corps fins occupent deux couches adjacentes entre la brique de toit
et l'arbalétrier existant ; deux fermes restent nominalement ancrées
aux deux murs, cinq pas encore.

Cette configuration est un vrai sous-assemblage de pièces identifiées,
avec LDraw de la maison complète et LDraw local de ferme+mur+toit.

**Mais le coude a un degré de liberté.** Sans une fixation supplémentaire
suffisamment rigidifiée, il ne transmet pas une compression stable.
Aucune notice définitive et aucune liste de commande ne doit en découler.

## Ordre d'insertion à tester dans une prochaine conception

1. 3700 sous rail 3460 à deux tenons, avant pose définitive des panneaux.
2. 2780 au trou de 3700, puis lien fin 32017.
3. Deuxième lien fin 32017 accroché par 2780 à l'arbalétrier 32278.
4. Fermer le coude par la troisième 2780 depuis la face accessible.
5. Tester l'encombrement réel du collier central, les extrémités
   des broches et leurs parcours d'insertion ; ces étapes ne sont
   **pas entièrement prouvées** par le seul LDraw et les cylindres.
6. **INTERDICTION** de charger la toiture sur ce coude libre.

LDraw est une représentation géométrique de pièces, pas un certificat
de contraintes ou d'engagement des clips. La future architecture doit
être soit triangulée avec un contreventement réel, soit remplacée par
des poutres/pannes posées sur des appuis muraux documentés, en limitant
les portées. Cette décision nécessite arbitrage GRAND-PÈRE, sans
repartir dans des essais de tolérances indéfinis.
