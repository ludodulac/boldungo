# Mission A-2 — interfaces réelles avant validation

Départ : PR #929 DRAFT ; branche `feat/lego2-mission-a-stacked-slope-test`.
`main`, GUIDED-004 canonique et anciennes variantes non modifiés.

Le micro-module extrait deux rangs internes (`j=1,2`) de A1 de **20 tenons de largeur**, avec deux pans `30363`, deux assises de briques `3003`, des supports verticaux 2×2 et une baseplate officielle `3811`. Il ne reconstruit pas les murs ou la maison entière.

**Deux candidats maximum** : faîtage d'origine par deux plaques `3023b` 1×2, ou capot par une plaque `3022` 2×2, qui possède des tubulures et une géométrie distinctes. Les exports distincts permettent de comparer sans remplacer l'existant.

LDraw miroir officiel version figée `c43ed06a128a10ed65675166bf42eb6fd608b9b0`. L'algorithme reprend `LDrawLibrary` et `check_collision`; il ne convertit jamais un `COLLISION` en connexion prouvée. Il prend des échantillons de descente verticale à 48, 32, 24, 16, 8, 4, 2, 0 LDU : **une absence de collision sur ces échantillons ne démontre pas une trajectoire continue sans intersection**.

L'objectif est de sortir l'ordre LDraw et les faits, sans annoncer de certification structurelle ni lancer le transfert à A1 tant que la preuve géométrique de chaque raccord manque. Les contacts simples et alignements dans un graphe nominal restent distincts d'une connexion stud/anti-stud validée.

**Point de vigilance préexistant :** le pas de 3 tenons du modèle A1 ne met pas nécessairement le tenon du rang inférieur sous un tube du suivant. La géométrie réelle des `stud4a/stud4s` aux Z=-10,-30,-50 de `s/30363s01.dat` doit rester autoritaire : ne pas supposer une embrayage `30363→30363` pour seulement justifier un graphe.
