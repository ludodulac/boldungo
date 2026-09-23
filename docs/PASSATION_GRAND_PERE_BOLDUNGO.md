# PASSATION GRAND-PÈRE BOLDÜNGO

État vérifié au jalon expérimental 071. La réalité GitHub et les artefacts réels priment sur ce document.

## Règles invariantes
- Inconnu reste inconnu. Plausibilité architecturale != preuve.
- SAME cue != SAME_PHYSICAL_OBJECT. DISTINCT cue != DISTINCT_PHYSICAL_OBJECTS.
- CANDIDATE != vérité. COMPARABLE_VISUAL_PROPERTY != même feature/objet.
- Non-visible != absent. Occluded != absent.
- Aucune inverse/converse automatique, aucune géométrie/topologie cachée.
- Les photos privées de contrôle ne sont jamais une entrée runtime.
- Aucun hardcoding real-house-5. Aucun merge main sans autorisation explicite.

## Chaîne 065 → 070
### 065 — mémoire négative discriminant
Branche experiment/identity-negative-memory-065, HEAD final 1231023b5fb50663023f87c719cc157f7c08eb4b, PR #775.
Le NO_RELIABLE_DISCRIMINANT 064 est persisté par signature de preuve stable et survit save/reload. Identité non résolue.

### 066 — graphe de contraintes du monde
Branche experiment/multiview-world-constraint-graph-066, HEAD 057d1563dae0e8f7c74e34084ae6aca9aedf29f2, PR #776.
Projection déterministe du Workspace, sans second truth store : nodes, constraints, components, competing organizations, missing constraints, contradictions.

### 067 — planner de contrainte manquante
Branche experiment/missing-constraint-perceptual-planner-067, HEAD f7c158682d04daa7c5c0352a79e59f403a32d651, PR #777.
Sur l'incertitude sidewall P2/P4 : NO_DISCRIMINATING_MAPPING. Manques structurés identifiés : cross-observation property correspondence puis property-outcome mapping.

### 068 — correspondance de propriétés
Branche experiment/cross-observation-property-correspondence-068, HEAD 0b0245d62e677f17be6bed4dcbd1d2c016022805, PR #778.
Retour visuel réel : une correspondance obs_p2_side_wall/upper_window ↔ obs_p4_rear_wall/upper_left_window au niveau COMPARABLE_VISUAL_PROPERTY. Aucune promotion identitaire.

### 069 — mapping propriété → organisations
Branche experiment/property-outcome-world-mapping-069, HEAD 8bc31bc1adcdb661798655e6b693774cf331be61, PR #779.
Retour réel : NO_RELIABLE_MAPPING, mappings=null. Le mapping fail-closed n'a sélectionné aucune organisation.

### 070 — jalon du monde actuel
Branche experiment/current-world-visual-milestone-070, HEAD b27b6a7454aee8fac495ddf5ff580bb47cf5fae8, PR #780.
Mémoire négative 069 persistée, save/reload PASS. État : 22 observations, 4 candidats multivues, 3 relations perceptives, 1 correspondance de propriété, 1 incertitude ouverte, 2 organisations concurrentes, 26 nodes, 34 constraints, 15 components, 11 insufficiently connected, 0 contradiction.
Jalon HTML qualitatif produit, sans Scene/LEGO/géométrie inventée.

## 071 — connectivité multivue globale
Branche experiment/global-multiview-connectivity-071, base exacte 070.
Diagnostic : les 11 composantes insuffisamment connectées sont mono-photo. Aucune ne contient de candidat inter-vues; une seule contient une relation locale. Toutes les observations concernées ont une ROI et des propriétés structurées. Le déficit principal est donc l'absence de preuve inter-vues, particulièrement pour les observations des photos 1 et 5.

Audit 062 → 063 → Workspace :
- category_proposal est conservé sous LocalObservation.proposed_category (le renderer 070 avait utilisé le mauvais nom);
- photo_index, ROI, visibilité, noms des observable_properties et observed_property_states sont conservés;
- les valeurs de observable_properties du dict 062 sont appauvries en simple set de noms à l'ingestion;
- observer_comment et bootstrap_id ne deviennent pas des champs du Workspace;
- cues d'identité, relations et ambiguïtés riches sont conservés; le bootstrap 062 avait 0 ambiguïté.

Conclusion 071 : les preuves déjà acquises ne suffisent pas à créer honnêtement beaucoup plus de connectivité. Une acquisition visuelle globale cinq-vues est nécessaire. Un unique batch générique est construit : il transmet les 22 observations comme pool, marque les observations des composantes fragmentées FRAGMENTED et les autres ANCHOR, conserve candidats/cues/relations/correspondances/mémoires négatives, et demande en une réponse plusieurs connexions pixel-grounded. Aucun produit cartésien observation×observation.

STOP au contact visuel 071 : ne simuler aucune réponse. Après retour réel, importer uniquement les éléments validés et remesurer le graphe avant toute Scene/LEGO.


## 072 — ingestion réelle de la passe globale 071
Branche experiment/ingest-global-connectivity-072, base exacte 071.

Le vrai response 071 est CONNECTIVITY_EVIDENCE_AVAILABLE : 0 candidat d'identité, 0 cue d'identité, 3 correspondances de propriétés, 8 relations VISIBLE_WITHIN/OBSERVED, 2 continuations, 0 ambiguïté. Validation stricte contre le request réel : toutes les entrées sont valides, aucune rejetée.

Déduplication : les 3 correspondances et 8 relations sont nouvelles. Les deux continuations (P1 roof edge et P5 roof edge = CONTINUES) existaient déjà et ne sont pas comptées comme gain.

Le Workspace est save/reload sans second truth store. Aucune identité n'est promue. COMPARABLE_VISUAL_PROPERTY reste perceptif; VISIBLE_WITHIN reste relation OBSERVED; CONTINUES reste état observé.

Correction de projection révélée par 072 : le graphe 070 ne projetait pas les property_correspondences persistées. 072 les projette désormais explicitement comme contraintes PROPERTY_CORRESPONDENCE / COMPARABLE_VISUAL_PROPERTY. Ce changement ne signifie jamais SAME_PHYSICAL_OBJECT, SAME_SURFACE, CONNECTED_TO ou ADJACENT_TO. Sur le baseline avant ingestion 071, cela porte le comptage de contraintes de 34 (ancien renderer 070) à 35, sans changer les 15 composantes car la correspondance 068 P2/P4 reliait des observations déjà dans la même composante via le candidat.

Mesure avant 071 avec la projection corrigée : 22 observations, 4 candidats, 5 cues, 1 correspondance, 3 relations, 2 continuations, 0 ambiguïté, 26 nodes, 35 constraints, 15 components, 11 insufficient, 1 open uncertainty, 0 contradiction.
Après 071 : 22 observations, 4 candidats, 5 cues, 4 correspondances, 11 relations, 2 continuations, 0 ambiguïté, 26 nodes, 46 constraints, 6 components, 2 insufficient, 1 open uncertainty, 0 contradiction.
Deltas : correspondances +3, relations +8, constraints +11, components -9, insufficient -9; tout le reste 0.

Composante principale après 071 : les ouvertures P1 et front_wall sont réunies localement, puis front_wall possède un pont perceptif COMPARABLE_VISUAL_PROPERTY vers P2 side_wall. Via les preuves déjà présentes, cette composante inclut aussi P2 upper_window, P4 rear_wall/upper_window/terrace et leurs candidats concernés.
P1 roof_edge et P5 roof_edge forment une composante multivue séparée via COMPARABLE_VISUAL_PROPERTY.
P5 near_window + side_wall forment encore une composante mono-photo; P5 n'a donc aucune identité physique établie malgré le pont perceptif de toiture.
Les deux seules composantes insuffisantes restantes sont obs_p3_tree seul et {obs_p5_near_window, obs_p5_side_wall}.

Au niveau photo, les preuves explicites forment désormais une chaîne perceptive couvrant les cinq vues : P1-P2, P1-P5, P2-P3 et P2-P4 (plus les liens existants). Cette connexité photo-level n'est pas une fusion d'identités physiques.

Décision 072 : WORLD_HYPOTHESIS_READY. Justification mécanique : les cinq photos appartiennent désormais à un graphe perceptif connexe au niveau des vues; 9 des 11 composantes insuffisantes ont disparu; il reste seulement 2 îlots mono-photo; aucune contradiction; l'incertitude physique sidewall reste explicitement ouverte. La future couche WorldHypothesis doit donc être qualitative, révisable et multi-organisation, jamais une Scene métrique : elle peut agréger uniquement les contraintes explicites, conserver candidats/alternatives/provenance/niveaux épistémiques, distinguer liens perceptifs et assertions physiques, et être reconstruite/révisée à l'arrivée de nouvelles preuves.

Aucun nouveau producer, request, discriminant, Scene, LEGO ou NOTICE en 072.


## 073 — première WorldHypothesis qualitative
Base : experiment/ingest-global-connectivity-072 @ c09f2e3b9d7e1d5005cae49ce001ff6ff5911cc7.
Branche : experiment/qualitative-world-hypothesis-073.

073 introduit WorldHypothesis comme projection déterministe et jetable du MultiViewWorkspace + MultiViewWorldConstraintGraph. Elle n'est pas stockée dans MultiViewWorkspace et se reconstruit à l'identique après save/reload.

État réel construit : 2 organisations concurrentes, correspondant exactement à l'unique incertitude ouverte identity-uncertainty-idc_sidewall_p2_p4 : branche same_physical_object et branche incompatible. Aucune branche n'est choisie. Les deux organisations partagent 19 observations du monde central et gardent explicitement non rattachées obs_p3_tree, obs_p5_near_window, obs_p5_side_wall. Les 4 identity candidates restent CANDIDATE.

Chaque assertion WorldHypothesis conserve type de preuve, niveau épistémique et provenance observation_ref/photo_index/ROI. Les niveaux OBSERVED, CUE, COMPARABLE_VISUAL_PROPERTY, CANDIDATE, AMBIGUOUS et EXHAUSTED présents dans l'état courant restent distincts; UNKNOWN reste une valeur licenciée par le modèle et n'est pas inventée quand aucune assertion UNKNOWN n'existe. Aucune connexité ne promeut une identité ou une topologie physique.

proposed_category : le champ était déjà conservé par LocalObservation et l'import 063 lui attribue certainty.category=PLAUSIBLE. 073 l'expose donc comme SemanticProposal au niveau CANDIDATE, avec la certitude category existante et la provenance ROI. Il ne devient jamais vérité physique.

Perte des valeurs de propriétés : RichBootstrapObservation 062 porte observable_properties comme dict valeur, mais l'import 063 ne conservait que set(keys). Correction au premier responsable : LocalObservation ajoute observable_property_values, optionnel/rétrocompatible, et l'import riche conserve dict(item.observable_properties) tout en gardant observable_properties=set(keys) pour compatibilité. Aucune valeur n'est interprétée par son texte.

Test de valeur architectural : ARCHITECTURAL_ORGANIZATION_READY. Critères mécaniques satisfaits : cinq photos présentes dans le réseau, 19 observations dans le core rattaché, 0 contradiction, relations OBSERVED VISIBLE_WITHIN entre propositions d'ouvertures et surfaces, relation OBSERVED VISUALLY_IN_FRONT_OF entre la proposition de plateforme et une surface. Cela autorise un raisonnement futur sur de grandes parties architecturales qualitatives, pas une Scene métrique.

Un renderer HTML autonome 073 montre MONDE CENTRAL, ponts/relations avec niveaux épistémiques, deux organisations concurrentes, propositions sémantiques, incertitudes/mémoires EXHAUSTED et éléments non rattachés. Aucune géométrie 3D.

Aucun nouveau contact visuel, producer, request observateur, hardcoding real-house-5 runtime, Scene finale, LEGO ou NOTICE.
