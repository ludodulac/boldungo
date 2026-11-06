# BOLDÜNGO — contrat de DESIGN LEGO RECONNAISSABLE (premier prototype exécutable)

## Orientation donnée par le propriétaire
Une maison LEGO doit être **immédiatement reconnaissable** par une personne qui connaît le bâtiment. La silhouette, les formes, les proportions visuelles, les couleurs et les petits détails caractéristiques priment sur le centimètre exact. Les vraies pièces LEGO et la solidité restent nécessaires dans une **étape ultérieure de vérification**.

Un toit zinc est normalement composé de **plusieurs bandes / feuilles** ; le designer peut donc suggérer de multiples joints et pièces, même lorsqu'aucun joint n'est net sur les photographies. **Il ne doit jamais présenter le nombre imaginé comme une observation réelle.** Même principe : gouttières, lames de bois, reliefs et bordures de poutres.

## Implémentation, portée et limitations
- `frontend/data/boldungo-lego-design-intent-v1.json` : exemple BOLDÜNGO, corrections de propriétaire, éléments signatures, de caractère, à interpréter et interdits visuels.
- `frontend/lego-design-brief-v1.js` : fonctions pures `validateLegoDesignIntent`, `createLegoVisualBrief`, `reviewLegoVisualProposal` ; réutilisables plus tard par un pipeline ou une interface.
- `tests/lego_design_brief_v1.mjs` : tests autonomes, exécutables via `node tests/lego_design_brief_v1.mjs`.
- `PLAN-L-V2.html` : schéma corrigé montrant le contact direct des deux terrasses et de la volée haute avec la façade.

**Ce qui est effectivement développé :** un contrat de données et un contrôle déterministe de fidélité qui détecte : absence d'un élément emblématique, séparation d'une terrasse ou escalier, toiture en escalier, ou présentation mensongère d'un détail inféré comme fait observé.

**Ce qui n'est pas encore développé :** analyse automatique des fichiers images par ce module, choix automatique des pièces LEGO, rendu du modèle, contrôle de stabilité ou prise en compte automatique dans le logiciel public. `visual_ready` signifie seulement que la **proposition déclarative** a passé la grille, pas que l'image 3D a été analysée ni que la maquette est assemblable.

**Principe durable :** un modèle qui a plus de briques mais ne ressemble plus à la maison doit être rejeté, même si des connexions géométriques semblent meilleures.
