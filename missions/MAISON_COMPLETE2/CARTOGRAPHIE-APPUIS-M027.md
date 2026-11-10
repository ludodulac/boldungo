# BOLDÜNGO — MISSION 027 — CARTOGRAPHIE DES APPUIS DE TOITURE

**Contrôle géométrique ciblé réellement exécuté : SUCCESS. 408 / 408 pentes examinées.**
Aucune pièce LEGO déplacée. Ni connexion porteuse ni constructibilité certifiées.

## Sources et traçabilité

- Modèle réel GUIDED-004 : `missions/B3/generated/GUIDED004-B3-1904.ldr` (blob `288c60fde76918128d8b955f78ebfa9afc2dfe8e`) : **1 904** instances et **408** pentes `30363.dat`, chaque identifiant conservé.
- Bibliothèque réelle épinglée : `pybricks/ldraw@c43ed06a128a10ed65675166bf42eb6fd608b9b0`, **69 fichiers téléchargés temporairement** par GitHub Actions.
- Moteur existant utilisé avec les connecteurs M026 (deux tenons supérieurs authentiques de `30363`). Vérification des poses et des boîtes des **véritables maillages LDraw**.
- Exécution unique : https://github.com/ludodulac/boldungo/actions/runs/42772172716 — job `map-guided004-b3-roof-supports-027` : **SUCCESS**.
- Artefact : `BOLDUNGO-M027-B3-408-ROOF-SUPPORT-MAP-NOT-CERTIFIED`, contenant le **rapport Markdown complet de 408 lignes de pièces** et le JSON exhaustif `CARTOGRAPHIE-APPUIS-M027.json` (**références, positions, orientations, candidates de soutien et connecteurs supérieurs**).

## Classification exclusive des 408 pentes

| Catégorie | Nombre | Portée exacte |
|---|---:|---|
| **A** — connexion nominale sous `30363` démontrée | **0** | Aucun logement inférieur de cette pente n'est encore documenté ; impossible d'affirmer un assemblage porteur sous la pente. |
| **B** — appui ordinaire inférieur **géométriquement possible**, fixation **non démontrée** | **60** | La projection X/Z d'un tenon supérieur de brique ordinaire existante recoupe celle de la pente et son plan vertical est dans la fenêtre prudente [−4,+8] LDU du point le plus bas du maillage 30363 ; ce critère est seulement une présélection. |
| **C** — aucune pièce d'appui identifiée **par cette méthode** | **4** | Aucune candidate proche relevée ; **pas** une preuve d'absence physique de support. |
| **D** — voisinage sous la pente géométriquement indéterminé | **344** | Pente voisine ou pièce ordinaire proche sans interface de fixation démontrée ; ne pas convertir en appui certifié. |
| **TOTAL** | **408** | Une et une seule catégorie par pente. |

- **75 paires pente/brique ordinaire candidates B** (certaines pentes ont plusieurs candidates).
- **360 pentes** présentent au moins une pente voisine potentiellement plus basse, sans emboîtement inférieur prouvé : elles restent B si une brique ordinaire proche est identifiée, sinon D.
- **46 pentes** présentent des alignements nominaux sur leurs **deux tenons SUPÉRIEURS**, soit **92 correspondances** au total. Ces connexions **sur le dessus** sont recensées séparément et ne démontrent absolument aucun appui sous la pente.
- **Aucune analyse des collisions des 1 904 paires n'a été relancée.** Les contacts matériels et la stabilité restent non certifiés.

## Paire réelle proposée pour la prochaine étude d'une connexion sous la pente

**Pente :** `roof-000048`, référence LEGO `30363.dat`, origine LDraw **(470, −816, 60)** ; matrice d'orientation (rangées) `[0,0,1 ; 0,1,0 ; −1,0,0]`.

**Candidate ordinaire :** `gable-000006`, référence LEGO `3004.dat`, origine **(480, −792, 50)** ; orientation identité. Elle appartient réellement aux **1 904 pièces** de B3, elle n'a pas été inventée ou placée spécialement.

Le tenon existant de la brique `3004` se trouve notamment à **(470, −792, 50)** LDU ; son plan nominal est à **0 LDU** du bord inférieur de la boîte du maillage de la pente. Cela **ne prouve ni contact entre les deux surfaces, ni présence de logement `anti_stud` sous `30363`**. Cette paire est une **priorité de diagnostic**, pas une solution validée.

## Pentes sans appui identifié (catégorie C)

| Pente | Origine LDraw (X,Y,Z) |
|---|---|
| `roof-000001` | (350, −768, 20) |
| `roof-000023` | (350, −768, 900) |
| `roof-000208` | (1270, −768, 20) |
| `roof-000230` | (1270, −768, 900) |

Elles sont localisées aux **quatre extrémités des rangées basses**. « Non identifié » ne signifie ni absence de matière de soutien ni que les quatre pièces tomberont.

## Zones à approfondir

Les classes D prédominent au milieu des rampants : la superposition projetée de pentes décalées en hauteur est observable, mais leur face inférieure et leur connexion n'ont pas été validées.

| Position Z dans la maison (LDU) | B possible | C non identifié | D indéterminé |
|---:|---:|---:|---:|
| 20 | 0 | 2 | 16 |
| 60 | 9 | 0 | 9 |
| 100 à 580, par rangée de 40 | 2 par rangée | 0 | 16 par rangée |
| 620 et 660 | 3 par rangée | 0 | 15 par rangée |
| 700 et 740 | 2 par rangée | 0 | 16 par rangée |
| 780 et 820 | 3 par rangée | 0 | 12 par rangée |
| 860 | 9 | 0 | 9 |
| 900 | 0 | 2 | 16 |

Le relevé **individuel de chaque pente** (408 lignes) est dans le rapport Markdown de l'artefact. Le JSON accompagne chaque pièce susceptible d'être située dessous avec ses **identifiants, références, coordonnées et transformations exactes**, et sépare aussi les éventuels alignements au-dessus.

## Signification stricte et limites

- La recherche B/D utilise la **géométrie réelle des boîtes de maillages**, les **positions nominales de tenons connus**, l'orientation et la hauteur (LDraw Y positif vers le bas). **Une boîte englobante ne prouve jamais un appui réel.**
- Aucune face inférieure `30363` n'est encore certifiée en tant que logement récepteur. On ne doit pas transformer la géométrie de proximité en connecteur fictif.
- Les 92 alignements supérieurs ne prouvent ni insertion, ni tenue mécanique, ni absence de collision avec le corps incliné.
- La fixation des pentes, l'emboîtement admissible, le contrôle de la matière solide et la stabilité de la toiture sont **NON DÉMONTRÉS**.
- Aucun modèle B3, pente, mur, pignon, terrasse, photo, ni règle physique modifiés ; PR #931 reste DRAFT et PR #941 intacte.

## Accès aux preuves

- [Exécution GitHub Actions et téléchargement de l'artefact exhaustif](https://github.com/ludodulac/boldungo/actions/runs/42772172716).
- Script réutilisable `scripts/map_guided004_b3_roof_supports_027.py` — inventaire et cartographie de voisinage **sans refaire les 1 904 collisions**.
