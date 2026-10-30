# VALIDATION-2 — dix pièces existantes, ordre de montage

Ce dossier est **indépendant** du logiciel public : aucune pièce ou position finale modifiée.

- [SEQUENCE-10.json](SEQUENCE-10.json) : export pour la visionneuse BOLDÜNGO existante, mode « Montage », dix étapes.
- [TRAJECTOIRES.json](TRAJECTOIRES.json) : positions initiales et finales, équations continues, chaque pièce déjà installée vérifiée.
- [RESULTAT.json](RESULTAT.json) : verdict généré par la CI ciblée, aucune certification physique.
- [sequence-mobile.png](sequence-mobile.png) : capture du test mobile, si réussi.

## Démonstration

Mouvement LDraw : (x, y - 48 + 48t, z), 0 ≤ t ≤ 1, orientation constante.
La méthode vérifie toute la translation, **pas un échantillon** :

1. Enveloppes exactes des corps rectangulaires officiels : absence de
   chevauchement des matières massives sur tout l'intervalle (séparation
   par les plans de contact des étages).
2. Pour chaque tenon sur chaque pièce déjà placée (y compris les tenons
   sans connexion), rayon 6 LDU / hauteur 4 LDU vérifiés dans
   `p/stud.dat` du miroir LDraw épinglé.
3. Pour toutes les faces triangulées du modèle LDraw déplacé dont la
   cote peut intersecter **à un instant quelconque** le tenon, contrôle
   exact de distance 2D entre projection du triangle et disque du tenon.
   Une possibilité d'interférence entraîne NON DÉMONTRÉ (sécurité).
4. Connecteur de support déjà présent exigé après insertion.

**Limites :** uniquement les briques rectangulaires et leurs tenons
LDraw documentés ; pas de résistance, efforts de friction, tolérances
plastiques, tenue de l'ouvrage, ni de toiture. Ne généraliser ni au
modèle 356, ni aux 408 pièces inclinées.

Ouverture en prévisualisation **sans modifier la visionneuse** :
`frontend/viewer.html?bundle=../missions/VALIDATION2/SEQUENCE-10.json`
sur une prévisualisation de cette branche avec le dépôt servi à sa
racine. La version publique GitHub Pages reste inchangée.
