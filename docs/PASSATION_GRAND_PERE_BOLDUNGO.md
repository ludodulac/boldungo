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
