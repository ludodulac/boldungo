# LEGO2-071 — Validité des appuis sous faîtage

## Correction ciblée

Une colonne LEGO 1×1 sur une pièce située à la bonne hauteur n'est **pas**
nécessairement ancrée. Le générateur 070 choisissait auparavant un hôte de
maçonnerie par simple recouvrement XY, sans montrer si ce mur était relié
à un socle réel.

071 réutilise `analyze_standard_brick_support_chain` pour repérer les
supports nominaux et `validate_connection` pour vérifier **chaque arête**
de la chaîne depuis l'hôte choisi jusqu'à la cote architecturale `z=0`.
Une connexion `UNKNOWN` ou une pièce flottante invalide cette proposition
locale : les nouveaux potelets ne sont alors plus proposés.

Les hôtes `roof_support` ne sont pas automatiquement assimilés aux murs
ancrés ; ils restent `UNKNOWN_HOST_OUTSIDE_WALL_SUPPORT_DOMAIN` tant que
leurs chaînes de charge propres ne sont pas documentées.

## Limites documentées

Une chaîne `DOCUMENTED_NOMINAL_WALL_STUD_PATH_TO_Z0` vérifie des interfaces
LEGO **nominales**, non une fondation, la solidité des liaisons, le poids de la
toiture ou les efforts de flambement. Le raccord supérieur du potelet au
couvre-faîtage, la connexion du couvre-faîtage aux deux versants, les
collisions préexistantes, et l'ordre de montage restent `UNKNOWN`.
Le statut de la maison reste **NOT_CERTIFIED**.

Les géométries et le contrôle des collisions LDraw de 070 sont conservés
sans relancer les expériences 066–069. Le projet reste non-mutant ;
GUIDED-004 garde ses 1 890 pièces.

## Tests

Tests 070 adaptés à des piles réellement connectées au niveau nominal.
Tests 071 : mur flottant, chaîne 1×1 jusqu'à z=0, interface non documentée
BRICK_1X4, support de toiture hors domaine, deuxième orientation de toit,
et base de mur non ancrée.
