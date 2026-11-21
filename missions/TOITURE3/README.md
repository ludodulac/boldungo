# TOITURE-3 — première rangée continue à cinq briques de toiture

**Conserve sans aucune modification** les 15 positions sources étudiées de B-3.
Les cinq vraies pentes LEGO `30363.dat` originales `roof-000336` à
`roof-000340` sont assemblées **sur un même support LEGO officiel
`3006.dat` (brique 2×10)**, au lieu de multiplier cinq `3002` qui se
chevaucheraient dans une rangée continue.

La brique inférieure `3622.dat` originale de TOITURE-2 est conservée,
et la brique supérieure `3622` de B-3 est **exclue seulement dans la
variante locale**. Le module TOITURE-2 à trois pièces reste intact.
Une pièce expérimentale `3006` est introduite, en remplacement local.

Les dix autres `30363` des rangées voisines `roof-000313`–`317`
et `roof-000359`–`363` sont étudiées comme voisines et conservées
intactes. **Elles ne sont pas déclarées attachées** à la structure.

## Pièces et preuves

- `B3-ORIGINAL-READONLY.ldr` : snapshot exact du blob Git B-3
  (1904 placements, dont 408 pentes), en lecture seule, copie,
  **jamais éditée**.
- `MODULE-CONTIGU-5.ldr` : 5 toitures 30363 originales + 1 3006
  expérimental + 1 3622 original.
- `VIEWER-7.json` : visualisation 3D **schématique**, sept étapes dans
  la visionneuse BOLDÜNGO existante.
- `BOM.json`, `PROVENANCE.json` : nomenclature, 15 positions étudiées,
  5 intégrées à l'expérience, références et positions certifiables.
- `CONNEXIONS.json` : joints inférieurs et deux cavités par toit.
- `COLLISIONS.json` : maillages réels et **voisins conservés dans B-3**.
- `INSERTION.json` : dégagement analytique continu vertical, ordre.
- `RESULTAT.json` : compteurs réels générés par CI ciblée.
- `toiture3-mobile.png` : capture navigateur mobile si validée.

Lien **prévisualisation locale de cette branche**, via serveur à la
racine : `frontend/viewer.html?bundle=../missions/TOITURE3/VIEWER-7.json`.

**Limite majeure** : la cheminée `3622` est la racine *locale*
du module. Aucune liaison porteuse à la charpente, aux murs porteurs
ou aux fondations n'est démontrée. Même si tous les contrôles locaux
PASS, **la toiture ne peut pas être déclarée structurellement assemblable
sur la maison** avant cette liaison indépendante de la cheminée.
Ni stabilité, ni efforts, ni tolérances de plastique vérifiés.
