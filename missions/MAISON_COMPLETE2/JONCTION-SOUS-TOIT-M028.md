# BOLDÜNGO — MISSION 028 — PREMIÈRE JONCTION SOUS LA TOITURE

**Verdict : C — INDÉTERMINÉ.** L'unique paire étudiée présente un contact de surfaces LDraw, mais **aucun emboîtement sous la pente n'est démontré** et **aucune impossibilité physique n'est démontrée**.

## Preuves et intégrité

- Modèle exact inchangé : `missions/B3/generated/GUIDED004-B3-1904.ldr` (blob `288c60fde76918128d8b955f78ebfa9afc2dfe8e`), **1 904 pièces**, dont **408 pentes**.
- Révision LDraw épinglée : `pybricks/ldraw@c43ed06a128a10ed65675166bf42eb6fd608b9b0`. **21 fichiers** LDraw téléchargés temporairement dans le runner, sans copie des fichiers tiers dans le dépôt.
- **Exécution ciblée SUCCESS :** https://github.com/ludodulac/boldungo/actions/runs/42794587345 — un seul job M028, aucun retour aux missions M020–M027 ni aux autres paires.
- **Preuves numériques :** artefact GitHub Actions `BOLDUNGO-M028-SINGLE-SLOPE-TO-GABLE-UNPROVEN`, contenant `PREUVES-JONCTION-M028.json` et la version automatiquement produite du présent rapport.
- Moteur existant : `LDrawLibrary`, `instance_from_dict`, `check_collision`, `find_connections` et `_tri_intersection_kind`. Aucune modification de moteur.

## Géométries exactes et transformations

| Propriété | Pente | Brique voisine |
|---|---|---|
| Identifiant B3 | `roof-000048` | `gable-000006` |
| Référence réelle | `30363.dat` | `3004.dat` |
| Origine LDraw (X,Y,Z) | **(470, −816, 60)** | **(480, −792, 50)** |
| Rotation LDraw | `[0,0,1; 0,1,0; −1,0,0]` | Identité |
| Nombre de triangles réels | **700** | **172** |
| Boîte réelle du maillage, min → max | (400,−820,40) → (480,−792,80) | (460,−796,40) → (500,−768,60) |

Les boîtes décrivent seulement les limites spatiales des maillages, **pas** les zones d'emboîtement.

### Deux tenons de la brique 3004 (source explicite)

Le fichier authentique `parts/3004.dat:18` inclut `parts/s/3004s01.dat`. Les lignes **23 et 24** de ce sous-fichier placent deux `p/stud.dat` :

| Tenon 3004 | Centre nominal monde (LDU) | Sommet du tenon monde | Centre dans le repère local 30363 |
|---|---|---|---|
| 1 | **(490, −792, 50)** | (490, −796, 50) | (10, 24, 20) |
| 2 | **(470, −792, 50)** | (470, −796, 50) | (10, 24, 0) |

Le tenon n°1, à **X = 490**, se situe au-delà de la boîte spatiale maximale de la pente (**X = 480**) : **il ne peut pas fournir, en l'état, la jonction sous cette pente**. Le tenon n°2 entre dans son empreinte ; c'est le seul candidat de cette brique au voisinage du dessous de la pente.

### Géométries de tubes sous la pente

`parts/30363.dat:16` contient `parts/s/30363s01.dat`. Le sous-fichier utilise de vraies primitives de **tube ouvert** `p/stud4a.dat`, et des segments de tube incliné `p/stud4s.dat`. Leurs transformations sont celles du modèle original :

| Source | Origine du tube locale 30363 | Origine d'axe monde | Écart horizontal au tenon candidat n°2 |
|---|---|---|---:|
| `parts/s/30363s01.dat:18` → `p/stud4a.dat` | (0, 6,667, −10) | **(460, −809,333, 60)** | **14,142136 LDU** |
| `parts/s/30363s01.dat:35` → `p/stud4a.dat` | (0, 13,344, −30) | **(440, −802,656, 60)** | **31,622777 LDU** |
| `parts/s/30363s01.dat:37` → `p/stud4a.dat` | (0, 20, −50) | **(420, −796, 60)** | **50,990195 LDU** |

Les fragments de tubes inclinés `stud4s.dat` apparaissent notamment aux lignes **34 et 36** du même sous-fichier. Les **deux tenons supérieurs** de la 30363 figurent séparément aux lignes 61–62 : ils ne démontrent aucun logement inférieur.

**Attention géométrique :** le centre d'un tenon qui s'engage dans le dessous d'une brique n'est pas nécessairement **confondu avec l'axe d'un tube central**. Le tenon peut se placer dans une zone entre un tube et les parois. Les distances 14,142136 / 31,622777 / 50,990195 LDU **n'excluent donc pas**, à elles seules, un emboîtement physique.

## Vérification réelle de l'unique paire

- **`check_collision` : `CONTACT`** selon les véritables maillages LDraw de cette paire ; **aucun croisement de triangles non coplanaires détecté** dans cette configuration.
- **`find_connections` : 0** connexion nominale reconnue entre ces deux pièces. Le moteur M026 sait reconnaître les **tenons supérieurs** de 30363, **pas les réceptions inférieures** de la pente.
- **Ce que montre le test :** un contact géométrique de maillages, avec un tenon 3004 sous l'empreinte de la pente et de vraies primitives de tubes sur le dessous.
- **Ce que le test ne montre pas :** un logement inférieur compatible explicitement identifié à la position locale **(10,24,0)**, avec une géométrie de réception démontrée, des tolérances et une trajectoire d'insertion vérifiées.
- Il serait faux de déduire une **connexion admissible** de ce simple contact. Il serait également faux de prononcer une **exclusion** par la seule non-coïncidence du tenon avec les axes des tubes.

## Verdict obligatoire et conséquences

**C — INDÉTERMINÉ.** Le chaînon probatoire manquant est la démonstration du **volume libre et de la géométrie de réception réellement utilisable sous `30363` au site local (10,24,0)**, puis de l'engagement d'un tenon réel dans cet espace. Les surfaces LDraw ouvertes ne fournissent pas automatiquement une qualification fiable des corps matériels ni des tolérances de montage.

La paire `roof-000048` / `gable-000006` reste dans la catégorie **appui possible, non démontré**. La conclusion ne peut pas être généralisée aux 59 autres pentes de catégorie B ni à l'ensemble de la toiture.

**Aucune pièce, pente, mur, pignon, terrasse, photographie, géométrie du modèle B3 ou règle de collision n'a été modifié.** Constructibilité, insertion et stabilité restent **NON CERTIFIÉES**.
