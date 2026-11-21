# TOITURE-6 — sous-ensemble RETENU après la seule campagne corrigée

**75 vrais éléments LEGO** figurent dans la version retenue : les 43 pièces
du module TOITURE-5, 31 briques originales B3 du mur latéral menant de
`wall-000021` à `wall-000719`, et **1 véritable baseplate 3811** à
(960, 0, 760).

**PASS mesuré :** les deux murs ont chacun 8 raccords exacts avec la
baseplate, la seconde colonne a 30/30 joints compatibles et l'insertion
verticale des deux pieds est sans obstruction analytique. Le module
TOITURE-5 et ses 5 pièces de toiture demeurent inchangés.

**STOP / exclusion prudente :** les quatre nouvelles briques 3006
de la liaison supérieure (la variante expérimentale 80 pièces) présentent
4 collisions interdites avec des pentes originales B3, première :
`TOITURE6-BRIDGE-D-3006` ↔ `roof-000223`. Le second appui
toiture→mur est donc **NON DÉMONTRÉ**, malgré 5/5 joints
nominaux compatibles en isolation.

La sixième pente `roof-000315` n'est **pas** retenue : insertion
bloquée selon le test conservateur par un tenon à
(1050,-840,610), avec une ambiguïté supplémentaire contre
`roof-000338`. Nombre de pentes retenues = **5**, pas 6.

**Deux colonnes attachées à la même baseplate locale** ne démontrent pas
deux supports de toiture indépendants, ni la résistance mécanique
ou l'ancrage au sol. Il n'y a aucune fondation complète certifiée.

`MODULE-RETENU-75.ldr` et `VIEWER-RETENU-75.json` sont
des fichiers dérivés par sélection pure des pièces géométriquement
justifiées, sans nouveau placement ni mutation B3 ou 019/356.
La vue 75 pièces n'a **pas** reçu de campagne Chromium distincte.
La vue expérimentale 80 pièces a eu un test navigateur PASS,
mais contient des pièces explicitement **non validées** et ne doit
pas être assemblée physiquement telle quelle.

Voir `RESULTAT.json`, `FONDATION.json`,
`DEUXIEME-APPUI.json` et `COLLISIONS.json` pour les preuves.
