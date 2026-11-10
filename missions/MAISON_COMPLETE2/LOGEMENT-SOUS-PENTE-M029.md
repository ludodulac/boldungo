# BOLDÜNGO — Mission 029 — Premier logement sous la pente

**Verdict C — DONNÉES INSUFFISANTES.** Un site potentiellement compatible est documenté, mais l'analyse ciblée des maillages signale des intersections pendant la dernière phase d'insertion simulée. Ni un emboîtement admis ni un obstacle matériel interdit ne sont donc démontrés.

## Sources vérifiées et périmètre

- Maison B3 GUIDED-004 **inchangée** : `missions/B3/generated/GUIDED004-B3-1904.ldr`, blob `288c60fde76918128d8b955f78ebfa9afc2dfe8e` ; **1 904** placements dont **408** pentes `30363.dat`.
- Une seule paire : **`roof-000048`**, pente `30363.dat` à **(470, −816, 60)** LDU (rotation `[0,0,1 ; 0,1,0 ; −1,0,0]`) et **`gable-000006`**, brique `3004.dat` à **(480, −792, 50)** LDU (rotation identité).
- Un seul tenon candidat étudié : centre monde **(470, −792, 50)** LDU, soit **(10, 24, 0)** dans le repère local de la pente. L'autre tenon de la brique, **(490, −792, 50)**, reste hors de l'empreinte de la pente.
- Maillages **véritables** de `pybricks/ldraw` révision épinglée `c43ed06a128a10ed65675166bf42eb6fd608b9b0` : **21 fichiers** de dépendances récupérés dans le runner uniquement.
- Exécution unique GitHub Actions **SUCCESS** : https://github.com/ludodulac/boldungo/actions/runs/42813333125. Ce succès signifie que **le diagnostic a été produit**, pas que le montage LEGO a réussi.
- Artefact `BOLDUNGO-M029-ONE-UNDERSIDE-POCKET-NOT-CERTIFIED` : rapport émis en CI + `MESURES-LOGEMENT-M029.json` (métriques, maillages, trajectoire simulée).

## 1. Géométrie réellement documentée autour du site

| Élément | Provenance LDraw | Géométrie observée |
|---|---|---|
| Tenon de la 3004 | `parts/s/3004s01.dat:24` → `p/stud.dat:19` | **Rayon 6 LDU**, hauteur **4 LDU** |
| Tube ouvert sous la 30363 | `parts/s/30363s01.dat:18` → `p/stud4a.dat:22` | Axe local **(0, 6,667, −10)**, rayon extérieur **8 LDU** ; le tronçon de tube descend nominalement vers **Y ≈ 24** |
| Paroi latérale intérieure | `parts/s/30363s01.dat:54` | Plan intérieur **X = 16 LDU** |
| Paroi frontale intérieure | `parts/s/30363s01.dat:48` → `p/box2-5.dat:22` | Plan intérieur **Z = 6 LDU** |
| Pièce en place | `parts/30363.dat:16` → `parts/s/30363s01.dat` | Transformations réelles inchangées |

Les dimensions proviennent **des primitives et de leurs transformations**, et non de la seule boîte englobante.

### Coupe nominale locale au voisinage du tenon

| Mesure | Valeur |
|---|---:|
| Distance entre centre du tenon local **(10, 0)** dans le plan XZ et axe du tube **(0, −10)** | **14,142136 LDU** |
| Jeu nominal cylindre–tube : **14,142136 − 6 − 8** | **+0,142136 LDU** |
| Jeu nominal tenon–paroi latérale : **16 − 10 − 6** | **0 LDU** |
| Jeu nominal tenon–paroi frontale : **6 − 0 − 6** | **0 LDU** |

Ces surfaces entourent géométriquement le tenon dans une zone pouvant jouer le rôle d'une **poche de réception**. Le modèle nominal est **tangent à deux parois** et très proche du tube : il ne prouve aucune tolérance suffisante, aucun frottement compatible et aucune capacité de retenue mécanique. LDraw ne qualifie pas automatiquement cette poche comme un connecteur `anti_stud` certifié.

## 2. Vérifications réelles de maillages et insertion hypothétique

Moteur existant, sans modification : `LDrawLibrary`, `check_collision`, `find_connections`. Maillages chargés : pente **700 triangles**, brique **172 triangles**, primitive authentique du tenon `stud.dat` placée dans le repère mondial de la pièce.

- **Paire entière en place : `CONTACT`** selon `check_collision`, déjà constaté en M028 et confirmé ici.
- **Connexions existantes reconnues : 0** selon `find_connections`. La M026 n'a documenté que les **tenons supérieurs** de 30363.
- Une trajectoire simple verticale a été simulée sur le **seul tenon réel isolé**, avec la pente maintenue fixe ; **aucune brique B3 n'a été déplacée**.

| Décalage virtuel du tenon vers le bas par rapport à sa position B3 (LDU) | Relation des véritables surfaces du tenon et de la pente |
|---:|---|
| +16 | `SEPARATED` |
| +12 | `SEPARATED` |
| +8 | `SEPARATED` |
| +6 | `SEPARATED` |
| +4 | `CONTACT` |
| +3 | **`COLLISION`** |
| +2 | **`COLLISION`** |
| +1 | **`COLLISION`** |
| 0 (position finale B3) | **`COLLISION`** |

**Écart important à ne pas masquer :** l'analyse de la **paire entière** donne `CONTACT`, tandis que le **tenon isolé** donne `COLLISION` dès qu'il entre plus profondément. Cela exige de déterminer **quelles faces provoquent le signal** (franchissement d'une surface, point-dans-maillage appliqué à des surfaces ouvertes, ou véritable contact matériel incompatible). La campagne M029 ne sépare pas ces causes et **ne justifie pas** de conclure directement à un obstacle rigide interdit. La trajectoire échantillonnée ne garantit d'ailleurs pas une insertion continue, ni celle de la brique entière.

## 3. Verdict et conséquence pour les appuis de toiture

### **C — DONNÉES INSUFFISANTES**

Les plans et le tube créent une **cavité nominale plausible** autour du site `(10,24,0)`, mais le passage virtuel du véritable tenon rencontre des alertes `COLLISION`. Les maillages LDraw de 30363 ne sont pas un modèle volumique fermé et certifié. Il manque donc une preuve sur la **nature matérielle des faces à cette profondeur**, sur la **capacité effective de recevoir le tenon** et sur le **chemin de montage**.

**Conséquence :** `roof-000048` / `gable-000006` reste un **appui possible NON DÉMONTRÉ**. Ne pas convertir les 60 pentes de catégorie B de M027 en appuis certifiés ; ne pas créer de connecteur inférieur dans le moteur.

### Prochaine action concrète, sans nouveau diagnostic géométrique identique

**Prototype physique minimal :** réunir une vraie pente LEGO **30363** et une vraie brique **3004** ; les placer avec les **mêmes orientations relatives** que dans B3, engager le tenon dans la poche candidate sans forcer, contrôler l'absence d'accrochage anormal et vérifier qu'une tenue mécanique existe. Photographier **dessous de 30363**, **dessus de 3004** et **joint assemblé**, en notant la référence des pièces. Si l'essai réel n'est pas possible, rechercher une **notice de montage LEGO authentique** illustrant explicitement une jonction 30363/3004 équivalente.

Cette vérification est nécessaire avant toute nouvelle règle de connexion. **Aucune pièce, pente, mur, pignon, terrasse, photographie, règle physique ou publication n'a été modifié.**
