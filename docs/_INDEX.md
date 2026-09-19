# Boldüngo — index documentaire sélectif

Commencer par `AI_START_HERE.md`. Cet index sert uniquement à atteindre rapidement la documentation spécialisée. **Ne pas charger tout `docs/`.**

## Cahier des charges produit

- [CAHIER_DES_CHARGES.md](CAHIER_DES_CHARGES.md) — référence produit consolidée : rôle des photos, réanalyse multivue, frontières Survey/Scene/LEGO, fidélité architecturale perceptive, contrôle humain et critères de réussite.

## Architecture canonique

- [ARCHITECTURAL_SURVEY_V01.md](ARCHITECTURAL_SURVEY_V01.md) — vérité observée/semantique et incertitudes issues des photos.
- [ARCHITECTURAL_SCENE_V02.md](ARCHITECTURAL_SCENE_V02.md) — vérité métrique/géométrique de la scène.
- [ARCHITECTURAL_ANALYSIS_PIPELINE.md](ARCHITECTURAL_ANALYSIS_PIPELINE.md) — passage des observations vers la scène architecturale.
- [ARCHITECTURE.md](ARCHITECTURE.md) — architecture générale du logiciel.
- [ARCHITECTURAL_LEGO_SOLUTIONS.md](ARCHITECTURAL_LEGO_SOLUTIONS.md) — adaptation de l'architecture aux contraintes LEGO.
- [ASSEMBLY_PLAN.md](ASSEMBLY_PLAN.md) — planification d'assemblage lorsque la tâche porte sur cette sortie.

## Raisonnement / validation

- [ARCHITECTURAL_REASONING_PASS.md](ARCHITECTURAL_REASONING_PASS.md) — passe de raisonnement architectural ; à lire seulement si cette étape est concernée.
- [BH-074_SURVEY_VALIDATION.md](BH-074_SURVEY_VALIDATION.md) — validation Survey historique/spécifique ; ne pas traiter comme état courant sans vérification.
- Les fichiers `BH-*` sont des traces ciblées de travaux/incidents. Les ouvrir uniquement lorsqu'un problème actuel pointe vers eux.

## API / déploiement

- [API.md](API.md) — contrats d'API.
- [ARCHITECTURE_DEPLOYMENT.md](ARCHITECTURE_DEPLOYMENT.md) — architecture de déploiement.

## Routage rapide

- Fait architectural absent ou incertain dès l'observation → `ARCHITECTURAL_SURVEY_V01`.
- Géométrie métrique fausse/perdue → `ARCHITECTURAL_SCENE_V02` puis pipeline.
- Scene correcte mais modèle LEGO faux/incomplet → `ARCHITECTURAL_LEGO_SOLUTIONS` puis code/tests du build.
- Export correct mais rendu faux → code/tests du viewer ; ne pas réécrire la Scene pour compenser.
- Problème de endpoint/contrat → `API`.
- Problème CI/déploiement → `ARCHITECTURE_DEPLOYMENT` + workflows réels.

## Principe de diagnostic

Suivre : **Survey → Scene → LEGO build → export → viewer** et trouver la première frontière où l'information devient fausse ou disparaît.

Le code, les données, les tests, la CI et le rendu réellement vérifié restent prioritaires sur cet index.
