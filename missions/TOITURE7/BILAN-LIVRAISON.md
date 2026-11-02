# BOLDÜNGO — TOITURE-7 : STOP technique conformément à l'ordre

Le code réel a été ajouté sur la PR #941, mais **la mission n'est pas certifiée**.
Le module de **75 pièces TOITURE-6 est conservé bit pour bit**, et ses 5
pentes restent les seules validées. Aucun élément supplémentaire n'est
qualifié d'assemblable.

## Travail réellement effectué

- Copie par identifiants de blobs Git du vrai `MODULE-RETENU-75.ldr` et
  de son `VIEWER-RETENU-75.json` : fichiers sous `TOITURE7` inchangés.
- Deux variantes B-3 distinctes, **uniquement expérimentales** :
  six briques LEGO officielles `3001.dat` (2×4) par variante,
  sous les rangées, aux plans Z=620 et Z=700, sans remettre les quatre
  longues poutres 3006 rejetées.
- Un script qui teste le vrai contact `roof-000223` ↔
  `wall-000719`, les vrais maillages des deux variantes et les pièces
  originales B-3 voisines, plus une vérification mobile Chromium
  **spécifiquement sur les 75 pièces retenues**.
- Deux campagnes CI au plus : [initiale #41467844665](https://github.com/ludodulac/boldungo/actions/runs/41467844665)
  et [correction #41468142253](https://github.com/ludodulac/boldungo/actions/runs/41468142253).

## Pourquoi nous nous arrêtons

L'analyse a échoué **techniquement avant les rapports mesurés** :
d'abord la géométrie officielle `3002.dat` manquante, puis après
la seule correction autorisée la géométrie `3004.dat` manquante dans
le catalogue LDraw téléchargé pour ce test. Ce n'est **pas** une
collision prouvée sur les nouvelles variantes.

Le contrôle de `roof-000223` contre `wall-000719` a bien été
calculé dans le processus Python avant son interruption, mais **aucun
rapport ni verdict n'a été conservé**. Son statut demeure
**NON DÉMONTRÉ**, et le deuxième chemin complet aussi.

Le test navigateur réel des 75 pièces n'a **pas été atteint**. Le
fichier de visualisation existe et est identique à l'export de TOITURE-6,
mais aucune capture de TOITURE-6 (80 pièces en échec) n'est présentée
comme un essai du modèle 75.

**STOP** : ne pas relancer de troisième CI dans cette mission, ne pas
annoncer un second appui, ne pas publier ni fusionner. La baseplate
3811 reste **locale**, et la mécanique réelle non démontrée.
