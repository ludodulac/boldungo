# 🧱 BOLDÜNGO — ANALYSE ARCHITECTURALE INITIALE (pré-construction)
Date : 2026-11-04 · Périmètre : **étude, pas modification 3D** · PR de travail : #931 (DRAFT)

## 1. Verdict immédiatement utile

**La source architecturale existe déjà, mais sa topologie externe n'est pas entièrement verrouillée.** Le problème à résoudre n'est pas « quelles briques acheter ? » mais **où se trouve exactement l'escalier en L par rapport au plan arrière Ouest et à la plateforme maçonnée**.

Plusieurs documents existants contiennent déjà les valeurs et objets nécessaires ; ne pas repartir de zéro. Le modèle LEGO 1 792 pièces a démontré des raccordements de tenons nominaux pour son toit en escaliers mais ne représente plus fidèlement le toit zinc incliné et ne constitue **pas** une preuve de constructibilité globale.

**Décision du propriétaire applicable au prochain modèle LEGO : arrière Ouest nu / sans cheminées volumineuses, MAIS escalier en L qui dépasse en arrière, plateformes correctement orientées et toit incliné.**

## 2. Sources effectivement consultées

| Source | Emplacement et portée | Statut |
|---|---|---|
| Décisions du propriétaire du 4 novembre 2026 | Échanges présents : simplification Ouest ; priorité escalier L ; fidélité + assemblages | CONSULTE / AUTORITÉ DE CIBLE |
| Cinq photos transmises dans l'échange | Photo 1 avant Est ; photo 2 côté Nord avec pavés de verre ; photo 3 ensemble terrasse Sud ; photos 4/5 escalier et côté Sud | OBSERVÉES VISUELLEMENT EN CONVERSATION ; pas un fichier GitHub versionné |
| Evidence GUIDED-004 | frontend/data/boldungo2-guided-004-evidence.json | LU : source historique annoncée « BOLDUNGO-LEGO2-57-photos-facades.zip » et vérité guidée |
| Scène d'origine | frontend/data/boldungo2-guided-004-real-scene.json | LU : 1 volume, 12 ouvertures, 2 escaliers paramétriques, 3 plateformes, 2 cheminées |
| Scène consolidée | frontend/data/boldungo2-guided-006-consolidated-scene.json | LU : 7+palier+9 ; 16 volumes de marches ; parapets ; plateformes distinctes ; cotes inférées |
| Dernière correction visuelle | frontend/data/boldungo2-guided-007-visual-corrections-scene.json | LU : 13 ouvertures, 2 pans, 31 plateformes, 34 éléments de garde-corps ; côté Sud inchangé par rapport à 006 |
| Test LEGO B-3 | missions/B3/RESULTATS-FINAUX-B1-B2-B3.md | LU : maison 1 904, connexion globale non certifiée, 408 pentes sans validation |
| Variante 1 792 | missions/MAISON_COMPLETE2/BILAN.md | LU : 296 briques de toit en marches, 172 cellules de couverture non remplies, essais limités |
| Précédente analyse photo méthodologique | docs/EXEMPLE_RAISonnement_ANALYSE_PHOTO.md | LU : observation → hypothèses → relations → inconnues |
| Règles d'orientation/topologie déjà écrites | frontend/brickhouse-survey-orientation-provenance-audit-v36.txt et ...stair-topology-audit-v37.txt | LUES : ne pas intervertir étiquette de capture et orientation réelle ; escalier multivolée ≠ segment |
| MODULE_003 ancien benchmark | docs/evidence/module-003-masonry-terrace-stair-041.json | LU PARTIELLEMENT : le benchmark possède une preuve qualitative 2 volées + plateforme + vide ; **NE PAS transférer ses coordonnées à GUIDED-004** |
| Archive photo 57 et guide source original | Nom attesté dans evidence.json, **absents du tree GitHub consulté** | **NON EXAMINÉS** : on ne peut pas déclarer une analyse exhaustive des 57 photos |

GitHub tree consulté sur la branche expérimentale : 1 396 entrées, 37 images jpg/png sous chemins différents, dont des copies benchmark ; **aucun fichier ZIP de 57 photos identifié**. Les photos d'un autre benchmark ne sont pas automatiquement une preuve interchangeable. Le dossier complet de 57 photos peut exister ailleurs : absence dans ce tree ≠ inexistence générale.

## 3. Observations directes sur les cinq photos de l'échange

| Photo de conversation | Ce qui est réellement visible | Ce qui reste non prouvé par cette seule vue |
|---|---|---|
| PHOTO-1 | Façade avant presque entière, 3 niveaux, 2 ouvertures par niveau (4 fenêtres haut/milieu, petite fenêtre basse à gauche, porte-fenêtre basse à droite), encadrements rosés/beige ; deux rampants, faîtage bas, petite cheminée/antenne | Côte exacte de pente, largeur réelle de chaque baie, faces cachées |
| PHOTO-2 | Côté le long d'une rue inclinée ; fenêtre haute, pavés de verre bas, égout/descente, variation importante du niveau du sol | Dimensions métriques des ouvertures et éventuelle propriété des bâtiments voisins |
| PHOTO-3 | Grand mur côté terrasse, garde-corps en bois en surélévation, retour d'angle, poteaux et contrefiches sous terrasse ; escalier maçonné sur le côté gauche | Distances exactes, implantation 3D exacte du coude de l'escalier |
| PHOTO-4 | Vue oblique montrant accès/volume maçonné avec un grand passage couvert sous plateforme, bord de la terrasse bois, poteaux | Situation complète des deux volées : l'une est masquée |
| PHOTO-5 | Escalier maçonné extérieur avec murs pleins et montée visible ; un volume de cheminée/ouvrage voisin est en arrière-plan ; circulation sous la plateforme ; terrasse bois en bord de vue | Identité et dimensions des pièces de cheminée, trajectoire complète de la volée cachée |

Pour les deux volées et leur ordre, utiliser la vérité propriétaire « 7 + palier + 9 », plutôt que prétendre dénombrer exactement les 16 marches depuis ces cinq vues. Les contours photographiques peuvent être masqués par perspective, plantes ou bâtiments voisins.

## 4. Repère et géométrie, EN NE CONFONDANT PAS LES AXES

**Référence d'orientation documentée et confirmée par le propriétaire dans l'evidence :**
- Est = façade principale / avant ; Ouest = dos / arrière ;
- Nord = côté droit vu de l'avant ; Sud = côté gauche ;
- maison : largeur Est 9,30 m CONFIRMÉE ; profondeur côté Sud ~8,20 m CONFIRMÉE approximativement ;
- dans GUIDED-004, x vers Nord, y vers Ouest, z altitude ; intérieur principal x=0..9,30, y=0..8,20 ;
- zone Sud extérieure x<0 ; au-delà du plan arrière Ouest y>8,20.

**Attention :** le fait qu'un escalier se situe sur la façade Sud n'empêche pas qu'il déborde du côté Ouest. La nouvelle consigne « doit dépasser en arrière » ne signifie pas supprimer l'escalier sous prétexte de façade Ouest nue.

Volume principal de GUIDED-007 : environ 9,30 × 8,20 × **7,20 m de haut INFÉRÉS** ; trois niveaux visibles. Le 7,20 m n'est pas une hauteur mesurée.

## 5. Constat par façade et objets essentiels

**Est / avant** : 6 ouvertures sur trois niveaux, alignements non rigoureusement réguliers, encadrements clairs colorés, petite fenêtre basse gauche et porte-fenêtre basse droite, pignon resserré, soubassement. Cotes horizontales/verticales des baies de GUIDED-007 restent des estimations malgré les corrections humaines.

**Nord / côté rue** : longue élévation relativement nue, fenêtre haute, ouverture basse de 6×5 pavés de verre selon la vérité guidée, rue en pente ; important de représenter le niveau du terrain et ne pas attribuer une ouverture voisine à la maison.

**Sud / côté extérieur habitable** : porte d'accès haut, autre porte-fenêtre, fenêtre haute, volume maçonné d'arrivée, terrasse bois surélevée à garde-corps et poteaux ; retour rétréci/diagonal côté Ouest, vide conservé sous le platelage, contrefiches visibles ; plateforme béton distincte de bois et passage couvert en dessous.

**Ouest / arrière** : historiquement une importante cheminée gainée de zinc appartenait à la maison. **Le propriétaire décide de l'omettre dans la maquette LEGO cible** et de laisser le mur arrière nu ; cette simplification ne supprime **pas** le débord du système d'escalier derrière le plan arrière. Cette distinction est prioritaire sur le rendu 1 792 précédent.

## 6. Escalier : véritable conflit de conception, pas nouveau problème de brique

### Points verrouillés au bon niveau de certitude

- **CONFIRMÉ PAR PROPRIÉTAIRE** dans GUIDED-004/006 : deux volées, 7 marches + palier intermédiaire + 9 marches, largeur ~1,12 m, palier presque carré.
- **OBSERVÉ PHOTOS** : escaliers et parapets maçonnés, escalier extérieur montant vers un niveau surélevé, volume couvert bas/vides, relation à la plateforme.
- **DÉCISION RÉCENTE** : le L doit dépasser derrière le dos Ouest, même si ce mur devient nu.
- **INCONNU** : position exacte du débord derrière le mur, longueur des deux volées, giron réel, niveau exact du palier, épaisseur et appuis du palier, cotes du passage sous plateforme.

### Contradiction entre modèles existants

1. GUIDED-004 représentait deux volées paramétriques : run-7 du point (-2,20 ; 0,70 ; 0) vers (-2,20 ; 1,75 ; 1,15), donc direction y ; run-9 ensuite vers (0 ; 1,75 ; 2,62), donc direction x. **Candidat ancien non gelé.**
2. GUIDED-006/007 a changé le sens des marches : run-7 avec progression x de -2,20 vers -1,12, puis run-9 avec progression y vers l'Ouest. Ce nouveau schéma respecte le L et une direction d'arrivée vers l'arrière, mais son bout supérieur arrive vers **y=4,50 m**, alors que le plan arrière de la maison est **y≈8,20 m**.
3. La demande récente **« l'escalier en L dépasse en arrière »** implique une **vérification prioritaire** de la partie qui déborde réellement au-delà de ce plan. Les coordonnées 006/007 **ne démontrent pas cette exigence**. Ne pas ajouter arbitrairement 3,70 m de briques : identifier le bon repère, ce qui dépasse réellement et la trajectoire à partir des vues d'origine.
4. Dans GUIDED-006/007 la première volée reconstruite donne des profondeurs de marches de **~0,154 m** sur x, tandis que l'autre donne **~0,257 m** sur y. Ces valeurs sont **inférées** et ne prouvent pas des girons réels. Pas de copie automatique dans un nouveau modèle LEGO.

**Verdict escalier : TOPOLOGIE DEUX VOLÉES CONNUE, ORIENTATION ET DÉBORD EXACT NON VERROUILLÉS (G2 FAIL).** C'est le premier point à traiter, avant toute construction de marches LEGO.

## 7. Terrasses : deux objets à ne jamais inverser

- **Plateforme maçonnée** (GUIDED-007) : footprint *inféré* 2,20×1,50 m, position ~x=-2,20, y=3,00, z=2,38 m, épaisseur 0,24 m, passage ouvert et deux supports. Ce volume **n'est pas un bloc plein**.
- **Terrasse bois principale** : footprint *inféré* 2,15×2,50 m, position ~x=-2,15, y=4,50, z=2,82 m ; poteaux bois, garde-corps et vides en dessous.
- **Retour terrasse bois Ouest** : footprint *inféré* 1,45×1,20 m vers y=7,00 ; l'ancien rectangle plus étroit est une **approximation du véritable retour oblique**, pas une surface rectangulaire observée.
- Les altitudes 2,38 et 2,82 ne prouvent pas une contremarche de 44 cm : ce sont des valeurs de scènes approximatives et pas forcément des niveaux de circulation comparables. Le propriétaire décrit une différence de niveau/marche entre surfaces ; valeur réelle à confirmer.

**Invariant architecture** : terrasse bois ≠ plateforme maçonnée ; aucune permutation Est/Ouest ; poteaux et diagonales ; vide visible ; au moins une interface entre modules, non confondue avec une collision mécanique.

## 8. Toit : second conflit important, mais pas la première mission

La maison possède une **vraie toiture à deux pans inclinés en zinc**, avec pignons, débords et faîtage. Les vues montrent une silhouette modérée, pas une pyramide en briques montantes.

- GUIDED-004 enregistrait **22°** avec source « inferred » (0,60).
- GUIDED-007, après correction visuelle humaine, a baissé la pente à **14°**, encore « inferred » (0,55).
- **Aucun de ces deux angles ne peut être proclamé une mesure confirmée.** La valeur exacte doit rester CONTRADICTOIRE/INCONNUE jusqu'à confirmation documentaire, ou un compromis explicite présenté au propriétaire.

La variante 1 792 remplace 408 pentes 30363 par 296 briques orthogonales et ferme partiellement les assemblages nominaux du toit, mais crée une toiture en escalier et 172 cellules de couverture vides. **Ne pas l'utiliser comme cible visuelle.** La structure porteuse et les pièces inclinées doivent être conçues ensemble, après verrouillage du volume hôte et des interfaces.

## 9. Programme de construction proposé : une bonne base avant les briques

**Sous-ensemble prioritaire E — escalier L autonome**, conçu dans son repère, incluant coude, parapets, arrivée, appuis et géométrie des vides. Ne pas le raccorder à une maison déformée. Le contrôle de l'extension arrière Ouest est une porte obligatoire.

**Module P — plateforme maçonnée et passage inférieur** : vérifier niveau, garde-corps, arrivée escalier et ancrage au mur ; doit pouvoir se joindre au module E sans inverser son orientation.

**Module T — terrasse bois** : indépendant, supports et contreventement, retour oblique, sa marche éventuelle vers P ; ne doit pas masquer le passage.

**Volume principal V — quatre façades et ouvertures** : repère/échelle unique, arrière nu selon la décision LEGO, conserver l'architecture 9,30×8,20.

**Module R — vraie toiture à pans inclinés** : charpente/tenons/clips/charnières adaptés et vraie surface oblique, pignons fidèles ; pas d'escaliers permanents.

**Assemblage final** : interfaces E↔P↔V, T↔V/P, R↔V ; maillages/insertions, nomenclature et notice seulement ensuite.

## 10. Bilan des portes qualité G0–G8

| Porte | Statut actuel | Motif |
|---|---|---|
| G0 Inventaire complet de 57 photos | **NON_TESTÉ / INCOMPLET** | ZIP non accessible dans le tree lu ; cinq photos de conversation + scènes analysées |
| G1 Repère cardinal | **PASS DOCUMENTAIRE PARTIEL** | Est avant, Ouest arrière, Nord droit, Sud gauche documentés ; orientation modèle à recouper |
| G2 Escalier : L et débord arrière | **FAIL** | 006/007 arrive à y≈4,50 m, alors que le plan Ouest est y≈8,20 m |
| G3 Mesures | **PARTIEL** | 9,30 m, ~8,20 m, 1,12 m et 7+9 verrouillés ; giron/pente/hauteurs incertains |
| G4 Fidélité multi-vues | **FAIL SUR PROTOTYPE 1 792** | toit escalier, terrasses/fenêtres contestées par propriétaire |
| G5 Interfaces structurelles | **NON_TESTÉ GLOBAL** | chemins de charges et attaches E/P/T/V/R pas conçus tous ensemble |
| G6 Connecteurs, collisions exactes | **NON_TESTÉ GLOBAL** | contacts nominalement positifs localement ; pas une preuve de tout le modèle |
| G7 Ordre de pose réel | **NON_TESTÉ** | aucune preuve continue d'insertion globale |
| G8 Essai LEGO réel | **NON_TESTÉ** | aucune certification de stabilité |

## 11. UNE SEULE PROCHAINE MISSION

Appliquer PROMPT-ESCALIER-L.md et **livrer un plan du système E en L**, avec : graphe de montée/descente, plan coté/altitudes provisoires, photo justificative de son extension réellement postérieure, parapets et passage dessous, trois méthodes LEGO et un seul choix recommandé.

**Critère d'acceptation préalable à la première brique :** la vue de dessus doit prouver le bon L, le sens de circulation, le lien à la plateforme maçonnée et l'extension effective derrière l'arrière Ouest. Si l'archive 57 photos reste introuvable, dire ce qui peut être décidé à partir des images présentes et ce qui est impossible à garantir ; ne pas inventer le débord.

Aucune modification du modèle dans cette mission, aucun merge, aucune publication, aucune pièce achetée.
