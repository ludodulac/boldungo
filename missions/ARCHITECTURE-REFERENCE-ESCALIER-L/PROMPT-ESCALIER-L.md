# BOLDÜNGO — PROMPT EXPERT : ESCALIER EXTÉRIEUR EN L
Version : 2026-11-04 · Priorité absolue · Mode analyse/conception, sans construction

## Objectif unique

À partir des photographies et des documents réellement consultés, déterminer la géométrie de référence de l'escalier **en L**, puis une architecture LEGO cohérente pour construire **un module indépendant raccordable à la maison**, sans improviser 1 000 briques.

**Invariants confirmés à retrouver dans les sources : largeur ~1,12 m, deux volées de 7 et 9 marches, palier intermédiaire approximativement carré.** L'ordre 7 puis 9 dépend du sens de montée enregistré. Conserver les murs et garde-corps maçonnés, le vide ou passage sous la plateforme, le raccordement haut et bas.

**Décision récente : façade arrière Ouest volontairement nue dans le modèle LEGO, mais escalier extérieur en L dépassant vers l'arrière toujours présent.** Les cheminées arrière sont supprimées du modèle cible, pas de la vérité photographique.

## A. Audit des sources avant raisonnement

- Lire PROMPT-MAITRE.md, le diagnostic ARCHITECTURE-INITIALE.md, les scènes GUIDED-004, GUIDED-006, GUIDED-007 et les anciens rapports LEGO de l'escalier.
- Recueillir chaque photo des 57 réellement accessible, surtout prises sous plusieurs directions ; cataloguer les vues 3 à 5 du dernier échange comme « PHOTO-CONVERSATION-3/4/5 », sans les renommer en fichiers GitHub.
- Relever les vérités utilisateur, sans inventer de mesure manquante, puis produire un tableau SOURCE/DATE/OBSERVATION/CONFIANCE.
- Garder un historique séparé des variantes descartées ; les exemples « real-house-5 » ou MODULE_003 ne deviennent pas automatiquement le même système métrique que GUIDED-004.

## B. Topologie à établir AVANT les dimensions

Pour chaque direction de circulation, distinguer :
1. Le pied sur le terrain (côté, point et altitude).
2. La volée basse (axe, sens, extérieur/intérieur du bâtiment).
3. Le bord d'arrivée de la volée basse sur le **palier de rotation**.
4. Le palier : 4 bords, angle du L, garde-corps et espace libre adjacent.
5. La volée haute (axe, sens, points bas/haut).
6. L'arrivée sur **la plateforme maçonnée** et son raccord à la maison.
7. Le débord réel derrière le plan Ouest.
8. Les murs/parapets de chaque volée, leur présence, éventuelle continuité et épaisseur.
9. Le vide de circulation **sous** la plateforme maçonnée ; ne jamais le combler en bloc.
10. L'indépendance de la terrasse bois : poteaux, garde-corps, retour biaisé, et éventuelle marche entre bois et béton.

Produire un graphe ordonné « terrain → volée basse → palier L → volée haute → plateforme maçonnée → accès maison », et le graphe inverse pour la descente. Croiser toutes les photos : si une image ne permet pas d'observer une volée, écrire OCCULTÉ, pas ABSENT.

## C. Repère et contradictions concrètes

Repère GUIDED-004 : x positif Nord, y positif Ouest (vers l'arrière), z vertical ; façade Sud sur x=0, façade Ouest sur y=8,20 m. L'escalier se développe à l'extérieur côté Sud (x<0), **et doit dépasser le plan arrière en y>8,20 m si le terme « dépasse à l'arrière » est bien métriquement applicable à la volée ou à son palier** ; ne jamais inventer la distance de dépassement.

Attention : GUIDED-004 a des extrémités de volées avec un sens différent de la version consolidée GUIDED-006/007. GUIDED-007 représente 7 marches suivant x (du dehors vers la façade) puis 9 suivant y (vers l'Ouest), avec une arrivée vers y=4,50 m — ce qui **ne démontre pas** le débord demandé au-delà de y=8,20 m. Le conflit est **G2 FAIL**, pas une géométrie figée. Rechercher les photos ou le guide et proposer deux hypothèses distinctes seulement si nécessaire. Le propriétaire a priorité sur une ancienne position inférée.

## D. Géométrie paramétrique

Construire une fiche métrique du système avec :
- largeur, comptage et ordre des marches ;
- giron/profondeur par volée, hauteur des contremarches ;
- niveau sol au pied, niveau palier, niveau haut, incertitudes ;
- emprise en plan des deux volées et palier ;
- longueur/largeur du palier, dimensions des parapets ;
- axes, sens de marche, offset par rapport au bâtiment ;
- base ou fondations ; points d'appui porteurs ;
- limites des zones vides et passage sous plateforme ;
- raccords du palier avec les deux volées ;
- raccord d'arrivée avec plateforme maçonnée et bâtiment ;
- interface séparée de la terrasse bois.

Pour toute dimension inconnue : fourchette justifiée OU valeur null, jamais une « cote exacte » inférée de pixels. La largeur 1,12 m et le comptage 7+9 restent inchangés. Le palier à peu près carré ne donne pas automatiquement 1,12×1,12 m.

Ne suppose pas qu'un volume de scène dessiné comme une marche possède un vrai giron : vérifier explicitement que le giron de GUIDED-006/007 (valeur reconstruite) est crédible et sourcé, sinon invalider la métrification.

## E. Six vues issues d'une seule source géométrique

Exiger : plan coté, élévation suivant chaque volée, façade Sud, vue arrière Ouest, dessous/volume vide et vue perspective. Les vues sont dérivées de **la même configuration**, pas dessinées séparément. Dans chaque vue distinguer la maison-hôte (gris), l'escalier en L (pierre/blanc), la plateforme maçonnée (gris clair), la terrasse bois (bois), la zone vide (hachurée) ; sans couleur porteuse de certitude implicite.

Contrôler : vue dessus lisible en L, sens de l'arrivée, distances relative au plan arrière, non-inversion des terrasses, pas de mur ajouté pour remplir le vide. Une vue de dessus fausse = STOP avant LEGO.

## F. Étude structurale LEGO : trois familles, puis un seul choix

Comparer (sans construire) :
1. noyau porteur maçonné et marches rapportées ;
2. deux volées en sous-assemblages, palier indépendant solidarisé à un cadre porteur ;
3. escalier modulaire appuyé sur murs latéraux avec renforts cachés compatibles et passages conservés.

Pour chaque option : pièces LEGO réelles envisagées, masse/volume approximatif, appuis, attaches au cadre, risques de basculement, démontabilité, séquence d'insertion, fidélité des parapets, conservation du vide, faisabilité d'une échelle de marches uniforme. Recommander **une** variante, documenter son motif de choix et ses réserves ; ne pas relancer indéfiniment l'optimisation d'une brique.

## G. Interfaces obligatoires

E0 — ancrage pied/escalier au terrain/à la base du modèle (réaliste ou hypothèse explicite).
E1 — volée 7 ↔ palier (liaison réelle, pas juxtaposition).
E2 — palier ↔ volée 9.
E3 — volée supérieure ↔ plateforme maçonnée.
E4 — plateforme maçonnée ↔ maison, avec accès haut.
E5 — parapets ↔ marches, appuis et garde-corps.
E6 — zone vide sous plateforme et éventuelles colonnes externes ; **ne jamais la boucher**.
E7 — distinction et éventuelle marche de liaison avec terrasse bois.
E8 — couplage géométrique à la façade Ouest simplifiée, débord et dégagement.

Chaque interface reçoit « face A, face B, coordonnées, connecteur LEGO éventuel, trajectoire d'insertion, voie de charge, collision, statut testé/non testé ». Ne prétendre aucune tenue physique à partir d'une position de tenon.

## H. Critères de validation et de STOP

- **T0 Sources :** photo(s) réellement accessible(s) pour les deux volées et leurs raccords ; sinon diagnostic préliminaire.
- **T1 Topologie :** 7 + palier + 9 dans le bon ordre, L correctement orienté.
- **T2 Position :** débord Ouest de référence démontré et compatible avec la façade Sud.
- **T3 Altitudes :** bas/palier/haut compatibles avec plateforme et terrain.
- **T4 Vide :** passage inférieur non comblé, plateformes béton/bois distinctes.
- **T5 Montage :** principe d'appui et connexions pour modules et parapets défini.
- **T6 Vérifications géométriques :** volumes, pièces, collisions et emboîtements selon un périmètre honnête.
- **T7 Viewer :** plan puis 4 façades puis perspective, sans permutation.
- **T8 Essai réel :** robustesse physique non certifiée tant qu'absence de construction.

Si T1/T2 échouent, **STOP construction**, retourner exactement la contradiction et la plus petite expérience photo/plan qui pourrait la résoudre. Un T6 positif ne compense jamais un T1/T2 faux.

## I. Livrable attendu de cette mission d'analyse

1. Carte des photographies utiles et des occultations.
2. Tableau observé / décision utilisateur / inféré / inconnu.
3. Graphe de circulation et définition du coude.
4. Plan coté **provisoire** avec toutes inconnues étiquetées.
5. Quatre élévations/projections à partir d'une géométrie unifiée.
6. Comparatif des trois solutions LEGO, choix d'une architecture.
7. Spécification de toutes les interfaces E0–E8.
8. Grille T0–T8 PASS/FAIL/NON_TESTÉ.
9. Une **mission de construction suivante** strictement limitée au module escalier L, seulement si T1, T2 et T4 sont vérifiés.

**Ne pas toucher au modèle 3D dans cette phase. Pas de PR fusionnée, pas de publication, pas d'achats, pas de fausse certification.**
