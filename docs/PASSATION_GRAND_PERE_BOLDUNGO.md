# PASSATION GRAND-PÈRE BOLDÜNGO — ÉTAT COURANT

Dernière mise à jour : 2026-09-23
But : permettre à une nouvelle conversation ChatGPT de reprendre le projet depuis le dépôt sans dépendre de l'historique d'un chat arrivé à sa limite.

## Règle de reprise

La réalité GitHub et les artefacts réels priment sur ce document. Une nouvelle conversation doit :
1. lire ce fichier ;
2. inspecter les PR expérimentales citées et leurs HEAD réels ;
3. vérifier les fichiers/tests réellement présents avant toute modification ;
4. ne rien fusionner vers main sans autorisation explicite de Ludovic.

## Objectif produit

À partir d'environ cinq photos ordinaires d'une maison, Boldüngo doit construire progressivement une représentation honnête d'un même monde physique, puis produire une maison LEGO reconnaissable, détaillée et physiquement constructible, et enfin une notice de montage. Les inconnues doivent rester inconnues. La plausibilité architecturale n'est pas une preuve.

Chaîne cible :
photos → perception multivue → MultiViewWorkspace → incertitudes/hypothèses → discriminants visuels → mise à jour du Workspace → Survey → Scene → LEGO → Notice.

Le travail actuel porte uniquement sur la perception multivue et la spirale de raisonnement pré-Survey.

## Invariants

- Survey = vérité sémantique/observée ; Scene = vérité géométrique/topologique ; LEGO = approximation constructive explicite.
- OBSERVED, CANDIDATE, AMBIGUOUS et UNKNOWN ne doivent pas être confondus.
- SAME cue != SAME_PHYSICAL_OBJECT.
- DISTINCT cue != DISTINCT_PHYSICAL_OBJECTS.
- non-visible != absent ; occluded != absent.
- support != proximité ; contact != connexion.
- aucune inverse/converse automatique.
- aucune géométrie/topologie cachée déduite de la plausibilité.
- les 17 photos privées de contrôle ne sont jamais une entrée runtime ni une source de règles spécifiques à real-house-5.
- le produit nominal doit fonctionner avec ~5 photos suffisamment informatives.
- pas de hardcoding real-house-5.
- pas de merge main sans autorisation explicite.

## Benchmark visuel courant

Cinq photos publiques :
frontend/benchmarks/real-house-5/01-original.jpg
frontend/benchmarks/real-house-5/02-original.jpg
frontend/benchmarks/real-house-5/03-original.jpg
frontend/benchmarks/real-house-5/04-original.jpg
frontend/benchmarks/real-house-5/05-original.jpg

L'ordre n'est pas censé porter une sémantique produit : ce sont des IDs stables. Le système doit inférer les correspondances multivues.

## État expérimental récent

Les PR suivantes sont DRAFT / NON MERGÉES au moment de cette passation. Toujours revérifier GitHub.

- PR #771 — experiment/rich-perception-bootstrap-062 — HEAD rapporté 0417e3ef4e8c6ae698683c96f680869f2c885afc.
  Mission 062 : enrichissement générique du bootstrap perceptif multivue 0.5. Ajout d'indices SAME/DISTINCT séparés, provenance photo+ROI, relations perceptives orientées, ambiguïtés perceptives, niveaux épistémiques. Pas de second moteur.
- PR #772 — experiment/rich-perception-ingestion-063 — HEAD rapporté e7bfbadf76a924990c6643070fdfbfbd028eda29.
  Mission 063 : contrat 0.5 rendu strict, ingestion de 22 observations, 4 IdentityCandidate, 4 cues SAME, 1 cue DISTINCT, 3 relation_evidence, 0 ambiguïté. Une vraie incertitude d'identité est créée pour idc_sidewall_p2_p4. Aucun cue n'est promu en vérité.
- PR #773 — experiment/identity-cue-discriminant-064 — HEAD rapporté 41897171308c1fecd45e9f21af641ee9f3384782.
  Mission 064 : réutilisation/extension de IdentityDiscriminantProducer afin de demander à l'observateur un test discriminant, pas une décision d'identité. Request réel produit pour idc_sidewall_p2_p4.

Avant cela, les PR expérimentales #734 à #770 ont construit progressivement la mécanique d'inquiry, persistance, continuation, identité, relation-pair, batch, dépendances et sélection d'impact. Elles ne doivent pas être fusionnées en bloc sans audit.

## Dernier contact visuel réel

Request :
identity-discriminant-producer-request-064.json

Candidat :
idc_sidewall_p2_p4

Hypothèses ouvertes :
- SAME_PHYSICAL_OBJECT
- DISTINCT_PHYSICAL_OBJECTS (token historique interne : incompatible)

Le request transmet un cue SAME et un cue DISTINCT avec provenance exacte et demande uniquement si les pixels permettent de construire un discriminant dont les outcomes diffèrent sous les deux hypothèses.

Réponse réelle de l'observateur :
identity-discriminant-producer-response-064.json

Résultat exact :
status = no_reliable_discriminant

Tous les champs du discriminant sont null.

Conséquence : NE PAS résoudre l'identité et NE PAS reproposer le même discriminant inchangé.

## PROCHAINE MISSION — 065

La conversation précédente a atteint sa limite avant de pouvoir exécuter cette mission. C'est la mission à reprendre.

Objectif :
1. ingérer strictement identity-discriminant-producer-response-064.json ;
2. valider request_id, identity_candidate_id, schéma et invariants ;
3. persister une mémoire négative indiquant que ce discriminant, avec les sources/cues/provenances actuels, a donné NO_RELIABLE_DISCRIMINANT ;
4. save/reload réel du MultiViewWorkspace ;
5. vérifier que l'identité reste non résolue, sans promotion SAME/DISTINCT, et que la même demande n'est plus reproposable ;
6. reprendre mécaniquement toute la spirale depuis la perception riche 062 : incertitudes, discriminants, reasoning dependencies, investigations à impact, candidats encore exploitables ;
7. ne pas fabriquer DISTINCT pour les trois IdentityCandidate qui n'ont qu'un cue SAME ;
8. ne pas revenir automatiquement à la combinatoire relation_pair ;
9. si aucun nouveau contact visuel n'est honnêtement possible, identifier et démontrer la première couche générique responsable, notamment vérifier si le manque est une représentation structurée des contraintes multivues permettant de construire un monde physique cohérent ;
10. si un nouveau contact visuel légitime existe, produire au maximum une salve de 5 investigations non épuisées, discriminantes, avec alternatives explicites et dépendance aval ;
11. si un request est produit, le sauvegarder, valider, SHA256 et fournir réellement le fichier téléchargeable ;
12. ne pas analyser les pixels, ne pas utiliser les 17 photos privées, ne pas corriger humainement le candidat, ne pas parser librement le texte des cues, ne pas toucher Survey/Scene/LEGO/NOTICE, ne pas merger main.

Rapport attendu MISSION_065 :
BASE / BRANCHE / HEAD / PR
RESPONSE_064_VALIDATION
OUTCOME_064
MÉMOIRE_NÉGATIVE_PERSISTÉE
SAVE_RELOAD
IDENTITÉ_RÉSOLUE
PROMOTION_SAME
PROMOTION_DISTINCT
DISCRIMINANT_064_REPROPOSABLE
INCERTITUDES_OUVERTES_APRÈS_RELOAD
IDENTITY_CANDIDATES_RESTANTS
REASONING_DEPENDENCIES
INVESTIGATIONS_À_IMPACT
TRANSITIONS_MÉCANIQUES_EXÉCUTÉES
PROCHAIN_CONTACT_VISUEL
SI_NONE_PREMIÈRE_COUCHE_RESPONSABLE
PREUVE_MÉCANIQUE_DU_BLOCKER
BATCH_PRODUIT
NOMBRE_INVESTIGATIONS
FICHIER / SHA256 / FICHIER_RÉEL_FOURNI
HARDCODING_REAL_HOUSE_5
PHOTOS_PRIVÉES
PIXELS_ANALYSÉS
RÉPONSE_VISUELLE_SIMULÉE
TESTS / CI
AUCUN_MERGE
STOP.

## Méthode générale

Le but n'est pas d'accumuler des micro-questions manuelles. Le mécanisme recherché est une spirale sur UN Workspace partagé :
SEE → générer incertitudes → hypothèses concurrentes → chercher preuve discriminante → observer → mettre à jour le même monde → répéter jusqu'à convergence ou IRREDUCIBLE_UNKNOWN.

Les investigations ciblées sont autorisées uniquement si elles lisent/écrivent le même état partagé et sont mécaniquement motivées par une incertitude réelle et une dépendance aval.

## Autres chantiers

NOTICE et CONSTRUCTION sont des workstreams séparés. Ne pas les mélanger avec la mission 065.
Le chantier Construction a un blocage historique de certification de connectivité de pente de toit LDraw.
Le chantier NOTICE a son propre banc frontend/instructions.html et son propre état de passation.

## À la reprise

Dire à Ludovic ce que GitHub confirme réellement, puis exécuter MISSION_065 sur une nouvelle branche expérimentale sans merge. Si les artefacts request/response 064 ne sont pas présents dans le dépôt, les retrouver dans les branches/PR expérimentales ou demander uniquement le fichier manquant à Ludovic. Ne jamais inventer leur contenu.
