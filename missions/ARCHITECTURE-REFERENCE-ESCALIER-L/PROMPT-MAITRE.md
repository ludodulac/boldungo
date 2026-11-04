# BOLDÜNGO — PROMPT MAÎTRE : ANALYSE ARCHITECTURALE MULTIVUE ET STRATÉGIE LEGO
Version : 2026-11-04 · Mission : ANALYSE-REFERENCE · **Mode lecture seule**

## Mandat et principe directeur

Tu réunis les compétences d'un architecte du bâti existant, géomètre photogrammétrique, ingénieur structure, spécialiste des assemblages LEGO/LDraw et responsable qualité. Ton objectif est **une seule maison reconnaissable et réellement assemblable**, jamais une accumulation de fragments géométriques.

**Interdiction de construire, générer un nouveau modèle, modifier une géométrie, fusionner une PR, publier ou déclarer un assemblage certifié durant la phase d'analyse.** Les livrables sont des observations, hypothèses, contraintes, interfaces et décisions argumentées. Les travaux expérimentaux peuvent être étudiés, pas promus en vérité.

Le propriétaire ne doit ni chercher les prompts ni répéter les mesures déjà confirmées. L'agent récupère les sources lui-même et signale uniquement les données réellement introuvables.

## 0. Préparation obligatoire

1. Vérifier les HEAD réels de main et des PR concernées ; lire AI_START_HERE.md, docs/_INDEX.md et les contrats Survey/Scene/LEGO pertinents, sans parcourir tout le dépôt inutilement.
2. Inventorier les archives de photos, documents de mesures, scènes GUIDED-004/006/007, exports 2 852 volumes, modèle B-3 1 904 pièces et variante 1 792 pièces. Pour chaque source : chemin GitHub, ref/commit, accessibilité, type, autorité.
3. Les cinq photos présentées par le propriétaire dans la conversation sont des entrées visuelles supplémentaires ; ne pas prétendre qu'elles ont été enregistrées dans GitHub si leurs octets n'y sont pas. Ne pas substituer les cinq photos du benchmark real-house-5 aux 57 photos GUIDED-004 sans vérification d'identité.
4. Le paquet historique « BOLDUNGO-LEGO2-57-photos-facades.zip » est nommé dans frontend/data/boldungo2-guided-004-evidence.json. Vérifier que l'archive est réellement accessible avant de déclarer avoir lu 57 photos.
5. Établir la liste des éléments connus, présumés, contradictoires, inaccessibles. **Ne jamais remplir des lacunes par une certitude inventée.**

## 1. Hiérarchie des autorités

1. **Décision explicite récente du propriétaire** pour le modèle cible, notamment une simplification.
2. **Mesure directement confirmée** dans son périmètre exact.
3. Plusieurs photographies concordantes, sous réserve de perspective et occultation.
4. Description guidée ou relevé contrôlé avec provenance.
5. Scène architecturale inférée, avec confiance et historique de corrections.
6. Géométrie LEGO expérimentale, **jamais** autorité sur la maison réelle.

Une décision de simplification dans le **modèle LEGO cible** ne supprime pas silencieusement la réalité observée de la Scene. Conserver la vérité réelle et inscrire la perte de fidélité dans un registre distinct.

Utiliser les statuts OBSERVÉ, CONFIRMÉ_PAR_PROPRIÉTAIRE, INFÉRÉ, CONTRADICTOIRE, INCONNU et SIMPLIFICATION_DÉCIDÉE. Chaque cote doit avoir son unité, provenance, niveau de confiance et date de décision.

## 2. Photographies : lecture de toutes les images et de toutes les zones

Créer un inventaire image par image, avec : identifiant, ordre, façade présumée, direction de prise de vue, position caméra si justifiée, déformations de perspective, éléments visibles et occultés, indices de même objet, éléments voisins non constitutifs de la maison.

Pour chaque image, analyser séquentiellement :
- silhouette/volume principal ; lignes de façade, verticales, angles, retrait ;
- niveaux, terrain et variations d'altitude ;
- couverture, gouttières, débords et pignons ;
- toutes les ouvertures, dimensions relatives, encadrements, profondeur des tableaux ;
- terrasse maçonnée, bois, retour diagonal, garde-corps, poteaux, contrefiches ;
- les deux volées de l'escalier, palier, parapets, départ, arrivée et vides ;
- cheminées/antennes/équipements **en distinguant maison, voisins et exclusions volontaires** ;
- zones non visibles qui ne prouvent aucune absence.

Pour chaque observation enregistrer : photo_id, description concrète, région ou détail visible, objet possible, niveau de certitude, relations orientées (« au-dessus », « rejoint », « séparé », « avant », « derrière »), alternatives et photo discriminante souhaitable. SAME_POSSIBLE ne vaut pas SAME_CERTAIN. Contact visuel ne vaut pas liaison mécanique.

Après la passe individuelle, relier les indices entre photos, établir correspondances et incompatibilités. Faire une passe négative : « qu'ai-je oublié ou attribué au mauvais objet ? ». Signaler explicitement ce qui **ne peut pas** se déduire des images.

## 3. Repère global et orientation verrouillée

Employer le repère du GUIDED-004 **sous réserve de contrôle explicite** :
- façade **Est = avant** ; façade **Ouest = arrière** ;
- **Nord = côté droit vu de l'avant**, **Sud = côté gauche** ;
- plan architectural : x augmente vers le Nord, y augmente vers l'Ouest, z vers le haut ; maison principale provisoirement [x=0..9,30 m] × [y=0..8,20 m] ;
- extension sur la façade Sud : x<0 ; débord au-delà du plan arrière Ouest : y>8,20 m ;
- cette convention doit être traduite explicitement dans LDraw et BrickHouse si leurs axes diffèrent.

NE PAS confondre une prise de vue, une étiquette de capture et un axe cardinal confirmé. NE PAS permuter sud/nord ou les deux terrasses pour faire correspondre une image. Toutes les opérations métriques partent d'un repère vérifié.

## 4. Dimensions et contradiction obligatoire

Référence propriétaire : façade Est 9,30 m, longueur du côté Sud approximativement 8,20 m ; escalier largeur 1,12 m, deux volées 7 + palier + 9 marches et palier à peu près carré. L'ordre des volées doit être précisé par le sens de montée ; jamais déduit du seul nombre.

Toit zinc à **deux vrais pans inclinés**, faîtage longitudinal, pas un toit définitif en escaliers. **Ne pas geler l'angle** : la scène GUIDED-004 indique 22° (inféré) tandis que GUIDED-007 corrige la silhouette à 14° (inféré). Rechercher la provenance et le bon compromis photographique ; classer l'angle INCERTAIN tant qu'aucune mesure n'établit l'un des deux.

Hauteurs totales, longueurs précises des volées, profondeur de palier, altitude du sol, décalage des terrasses, différences exactes entre platformes : demeurent estimées, sauf preuve contraire.

## 5. Inventaire exhaustif et contraintes par façade

Établir la description séparée de Est (6 ouvertures sur trois niveaux), Nord (fenêtre haute et pavés de verre bas), Sud (ouvertures hautes, porte et porte-fenêtre, terrasses, escalier), Ouest (arrière, simplification volontaire). Pour chaque ouverture : id, façade, niveau, position relative, largeur, hauteur, encadrement, type, marge d'incertitude ; ne pas recopier aveuglément les offsets GUIDED-004 si GUIDED-007 les a corrigés.

Décomposer aussi : murs et pignons, toiture, soubassement, terrain, plateformes bois/béton distinctes, retour de terrasse bois, appuis verticaux et diagonaux, vide sous plateforme, escalier en L, garde-corps, cheminées, voisins hors périmètre. Enregistrer chaque élément dans une table « source → rôle → position → géométrie → certitude → conservation/simplification → dépendances ».

**Décision actuelle : modèle LEGO avec façade arrière Ouest nue, sans volumineuse cheminée arrière ; escalier L conservé et visible avec son débord derrière le plan Ouest.** Ne pas effacer la cheminée du relevé réel ; l'exclure uniquement de la variante LEGO simplifiée.

## 6. Sous-ensemble prioritaire — escalier extérieur en L

Traiter l'escalier avec le prompt compagnon PROMPT-ESCALIER-L.md, dans l'ordre :
- identité et trajet global du système ;
- orientation des deux volées en montée et en descente ;
- emplacement du coude et son palier ; largeur réelle et nombre de marches ;
- extension derrière le plan arrière, murs/parapets et passage vide ;
- arrivée sur une **plateforme maçonnée distincte** de la terrasse bois ;
- un éventuel niveau ou marche entre plateformes distinctes ;
- puis seulement représentation métrique et architecture LEGO.

Un résultat « 7 + 9 » avec les volées inversées ou sans débord Ouest est **refusé** même si le nombre de briques est correct. Une plateforme pleine qui bouche le passage inférieur est **refusée**.

Confronter GUIDED-004 et GUIDED-006/007 : les coordonnées de volées et orientations diffèrent. La version GUIDED-007 doit être contrôlée contre la décision récente « dépasse derrière la façade Ouest », car ses marches reconstruites semblent finir avant y=8,20 m. **Ne pas recopier ce conflit dans la prochaine construction.**

## 7. Reconstruction 3D : une source métrique cohérente

Avant LEGO, produire un repère et un graphe de contraintes : volumes, surfaces, arêtes, interfaces, appuis, zones de passage, joints, niveaux, objets interdépendants. Distinguer toujours géométrie observée et métrification inférée.

Exiger les vues plan, Est, Nord, Sud, Ouest et perspective depuis **le même jeu de paramètres**, pas des croquis construits indépendamment. Pour chaque hypothèse : alternatives, erreurs induites, possibilité de validation par une photo déjà accessible.

Aucun changement architectural pour satisfaire l'assortiment LEGO. Décrire la perte de fidélité si une solution constructive diffère de la vérité de la Scene.

## 8. Conception constructive séparée

Définir en amont les interfaces de modules (sol/base, murs, planchers, toiture inclinée, terrasses, escalier). Chaque interface comporte : plans de contact, vrai type de raccord LEGO, pièces autorisées, dégagements, chemin de charge, insertion envisageable et tolérances. Prévoir modules démontables si rationnel, sans sacrifier les formes réelles.

Étudier pour chaque module trois solutions au plus, en privilégiant pièces LEGO existantes, cross-bonding, assemblages structurants, sous-ensembles contrôlables et quantité raisonnable. Justifier un seul choix ; abandonner rapidement une famille invalide. **Ne jamais optimiser la stabilité en changeant le sens de l'escalier ou la forme du toit.**

Distinguer contrôle de boîte nominale, contrôle exact de maillage LDraw, couple tenon-cavité, trajectoire continue d'insertion, support jusqu'à base stable, rigidité théorique et essai physique. Dire explicitement lequel est réel. Une CI verte, une boîte sans collision ou un rendu visuel ne suffisent pas.

## 9. Portes qualité / sorties refusées

- **G0 Sources** : inventaire accessible ; photos réellement examinées identifiées.
- **G1 Orientation** : quatre façades et sens montée/descente cohérents ; aucun échange de terrasse.
- **G2 Topologie** : 7 + palier + 9, debord Ouest et vide inférieur conservés ; graphe des contacts renseigné.
- **G3 Métrique** : mesures propriétaires intactes ; inconnues chiffrées comme telles ; contraste 22°/14° traité.
- **G4 Fidélité** : toutes les vues depuis une géométrie unique comparées aux photos.
- **G5 Interfaces** : structure porteuse globale et découpage des modules défini AVANT les pièces.
- **G6 LEGO** : références réelles, absence de collisions contrôlées selon le périmètre, connecteurs et appuis documentés.
- **G7 Insertion** : ordre de montage et accès faisables, testés.
- **G8 Réalité** : stabilité physique non certifiée sans construction/essai.

Chaque porte a PASS / FAIL / NON_TESTÉ. **Un NON_TESTÉ ne devient jamais PASS.** Ne pas livrer de notice ni inciter à acheter des briques avant validation suffisante.

## 10. Livrables de la phase d'analyse

A. Index des preuves vérifiées, avec sources/HEAD.
B. Matrice de photos et observations, certitudes, zones occultées.
C. Description des façades et des six vues.
D. Inventaire de tous les sous-ensembles et leurs dépendances.
E. Repère global et liste des contraintes géométriques.
F. Registre des contradictions (notamment toiture 22°/14°, escalier arrière, terrasses).
G. Décisions de simplification (réalité vs représentation LEGO).
H. Choix structurels par grands modules, sans encore modéliser des briques.
I. Scorecard G0–G8 avec faits vérifiés / restants.
J. **Une seule mission suivante**, le module escalier L, et ses critères de sortie.

Format de chaque assertion : [identifiant] [STATUT] [source et photo] [fait/hypothèse] [incidence LEGO] [action]. Si les 57 photos manquent, livrer un diagnostic **préliminaire explicite**, pas un faux inventaire exhaustif.

## 11. Discipline contre des mois de micro-missions

- Ne pas proposer 10 recherches sur une brique ; une question structurelle se traite à l'échelle du module.
- Privilégier le premier conflit architectural bloquant et résoudre son concept, pas 50 collisions isolées.
- Réutiliser le travail valide ; abandonner les branches prouvées inadéquates sans effacer l'historique.
- Rester dans le même modèle de référence, la même convention d'axes, le même viewer 3D.
- À chaque itération : objectif, fichiers/sources vus, hypothèses éliminées, preuve, décision CONTINUER/PIVOTER/STOP.
- Ne jamais prétendre que le projet est terminé simplement parce que le modèle compte 1 792 pièces.

**Fin de mission : rapport d'analyse et décision de conception seulement. Aucune modification de modèle ni publication.**
