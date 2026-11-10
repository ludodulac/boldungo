# BOLDÜNGO — MISSION 030 (REMPLACEMENT) — CONNEXIONS LDCad DE LA PENTE 30363

**Verdict : OUI — une connexion NOMINALE LDCad est décrite et les placements réels B3 correspondent exactement pour UN tenon de `gable-000006`.** Le moteur BOLDÜNGO **ne la reconnaît pas encore** (pas de logement inférieur 30363 dans `LDrawLibrary`). Il n'existe **toujours pas de certification de non-collision matérielle, insertion continue ou stabilité mécanique**.

Ce rapport **remplace et annule les livrables de l'ancienne M030 « preuve par notice LEGO »**. Le rapport sur les notices et le prototype de plaque 3035 ont été retirés de l'état courant de la branche, **sans réécrire l'historique Git**.

## 1. Sources réellement examinées (versions figées)

Source principale indépendante : **Roland Melkert, LDCad Shadow Library**, révision `9b1131fb1991f8c0bfc072325e4e12f6271aba35`, sous licence CC BY-SA 4.0.
- [`parts/s/30363s01.dat`](https://github.com/RolandMelkert/LDCadShadowLibrary/blob/9b1131fb1991f8c0bfc072325e4e12f6271aba35/parts/s/30363s01.dat) : quatre `SNAP_CYL` de genre **F**, déclinés sur quatre profondeurs de pente.
- [`parts/3004.dat`](https://github.com/RolandMelkert/LDCadShadowLibrary/blob/9b1131fb1991f8c0bfc072325e4e12f6271aba35/parts/3004.dat) : `SNAP_INCL` référençant `s\\3004s01.dat`.
- [`parts/s/3004s01.dat`](https://github.com/RolandMelkert/LDCadShadowLibrary/blob/9b1131fb1991f8c0bfc072325e4e12f6271aba35/parts/s/3004s01.dat) : `SNAP_CYL` genre **F** en dessous de la brique (non utilisé pour le tenon de ce cas).
- [`p/stud.dat`](https://github.com/RolandMelkert/LDCadShadowLibrary/blob/9b1131fb1991f8c0bfc072325e4e12f6271aba35/p/stud.dat) : `SNAP_CYL` genre **M**, section ronde, rayon 6 LDU, longueur 4 LDU.
- [`README.md`](https://github.com/RolandMelkert/LDCadShadowLibrary/blob/9b1131fb1991f8c0bfc072325e4e12f6271aba35/README.md), [`CONTRIBUTING.md`](https://github.com/RolandMelkert/LDCadShadowLibrary/blob/9b1131fb1991f8c0bfc072325e4e12f6271aba35/CONTRIBUTING.md), [`LICENSE.md`](https://github.com/RolandMelkert/LDCadShadowLibrary/blob/9b1131fb1991f8c0bfc072325e4e12f6271aba35/LICENSE.md).
- [Documentation officielle des métas LDCad](https://www.melkert.net/LDCad/tech/meta) : `SNAP_CYL`, `SNAP_INCL`, `gender`, `secs`, `caps`, `grid`, `pos`, `ori`.
- Géométrie LDraw correspondante, miroir épinglé `c43ed06a128a10ed65675166bf42eb6fd608b9b0` : [30363.dat](https://github.com/pybricks/ldraw/blob/c43ed06a128a10ed65675166bf42eb6fd608b9b0/parts/30363.dat), [s/30363s01.dat](https://github.com/pybricks/ldraw/blob/c43ed06a128a10ed65675166bf42eb6fd608b9b0/parts/s/30363s01.dat), [3004.dat](https://github.com/pybricks/ldraw/blob/c43ed06a128a10ed65675166bf42eb6fd608b9b0/parts/3004.dat), [s/3004s01.dat](https://github.com/pybricks/ldraw/blob/c43ed06a128a10ed65675166bf42eb6fd608b9b0/parts/s/3004s01.dat).
- Modèle propriétaire **inchangé** : `missions/B3/generated/GUIDED004-B3-1904.ldr` (blob `288c60fde76918128d8b955f78ebfa9afc2dfe8e`) : **1 904 pièces, 408 pentes**.

**Portée des contrôles :** lecture effective des fichiers sources et calcul exact des matrices et sites, **pas d'exécution du logiciel LDCad** ni de tests de maillages. Aucune copie de la bibliothèque tierce dans le dépôt.

## 2. Que signifient les instructions `SNAP_CYL` ?

Les commentaires `0 !LDCAD SNAP_CYL` sont des **métadonnées d'accrochage propres à LDCad**, distinctes des triangles LDraw. Ils indiquent des régions de connexion et des profils nominaux :
- **`gender=F`** : réception femelle ; **`gender=M`** : tenon mâle. Ce sont les deux profils complémentaires utilisés par les outils de *snapping* LDCad.
- **`secs=R 6 20`** : section **ronde (R)**, rayon nominal **6 LDU**, profondeur/longueur de la région **20 LDU** suivant l'axe local ; le tenon `p/stud.dat` est **`R 6 4`**.
- **`caps=one`** : une extrémité considérée fermée (pour la femelle, côté B/top suivant la convention LDCad) ; ce n'est pas une preuve de matière et de tolérances sur l'ensemble du volume.
- **`pos=0 24 0`** : origine des sites femelles dans le repère du sous-fichier `s/30363s01.dat`.
- **`grid=C 2 1 20 0`** : **2 colonnes X centrées** avec pas 20 LDU et 1 rangée Z sans décalage ; crée donc **X=−10 et X=+10**, pas X=0.
- **`ori` absent** : matrice unité (défaut défini par la documentation LDCad). La convention de leur axe nominal est **−Y**. Les rotations LDraw des sous-pièces puis des pièces B3 doivent être appliquées avant de confronter des sites.
- `SNAP_INCL` dans l'ombre 3004 inclut les informations de la sous-pièce de manière explicite. **Pour les deux tenons mâles de 3004**, c'est aussi la référence géométrique de `s/3004s01.dat` à `p/stud.dat` (avec matrices unité) qui fournit l'héritage de `SNAP_CYL` mâle.

**Attention :** la documentation LDCad précise que les informations héritées des fichiers géométriques sont fusionnées avec leurs « shadow files », sous réserve de la hiérarchie des sous-pièces. Une `SNAP_CYL` femelle `30363` n'a pas besoin d'être redéduite d'une boîte englobante.

## 3. HUIT sites de réception réellement définis sous 30363

Quatre enregistrements `F, R6` dans [`parts/s/30363s01.dat`](https://github.com/RolandMelkert/LDCadShadowLibrary/blob/9b1131fb1991f8c0bfc072325e4e12f6271aba35/parts/s/30363s01.dat), chacun dupliqué à X=−10 et +10 par `grid=C 2 1 20 0`.

| Rangée locale Z | Sites femelles locaux (X,Y,Z), LDU | Rayon | Profondeur femelle | Sites dans le B3 (X,Y,Z) monde, LDU |
|---:|---|---:|---:|---|
| 0 | (−10,24,0), **(+10,24,0)** | 6 | 20 | (470,−792,70), **(470,−792,50)** |
| −20 | (−10,24,−20), (+10,24,−20) | 6 | 14 | (450,−792,70), (450,−792,50) |
| −40 | (−10,24,−40), (+10,24,−40) | 6 | 8 | (430,−792,70), (430,−792,50) |
| −60 | (−10,24,−60), (+10,24,−60) | 6 | 4 | (410,−792,70), (410,−792,50) |

Les sites sont des **définitions de connexion publiées par LDCad** ; ils n'étaient pas reconnus dans notre moteur M026, qui ne reconnaît que deux tenons **sur le dessus** de `30363`.

## 4. Comparaison exacte de la paire existante dans B3

### Positions et orientations originales (aucune pièce déplacée)

`roof-000048`, `30363.dat` :
- Translation : **(470, −816, 60)** LDU.
- Rotation :
  ```
  [ 0  0  1 ]
  [ 0  1  0 ]
  [-1  0  0 ]
  ```
- Sous-pièce `s/30363s01.dat` incluse par `30363.dat` avec transformation **identité**, donc les huit sites F héritent de la rotation et translation de la pente.

`gable-000006`, `3004.dat` :
- Translation : **(480, −792, 50)** LDU.
- Rotation : **identité**.
- Sous-pièce `s/3004s01.dat` incluse par `3004.dat` avec transformation identité ; les deux `p/stud.dat` sont placés à **X=±10, Y=0, Z=0** localement. Leurs centres sont les deux sites mâles M R6×4.

### Calcul vérifié sans approximation

La pente transforme un point local `(x,y,z)` vers **`(470+z, −816+y, 60−x)`**.

| Site | Local | Monde | Connexion |
|---|---|---|---|
| **30363, réception F de profondeur 20** | **(+10,24,0)** | **(470,−792,50)** | Réception documentée LDCad |
| **3004, tenon M de longueur 4** | **(−10,0,0)** | **(470,−792,50)** | **Même centre monde : ΔX=ΔY=ΔZ=0 LDU** |
| 3004, autre tenon M | (+10,0,0) | (490,−792,50) | **Aucune** des huit réceptions de `30363` ne coïncide : deuxième tenon **non engagé** |
| 30363, autre réception F à Z=0 | (−10,24,0) | (470,−792,70) | Aucun des deux tenons de `3004` à cette position |

**Orientation :** les deux méta-profils `SNAP_CYL` utilisent l'axe local −Y par défaut. La rotation B3 de la pente conserve Y ; la brique 3004 est sans rotation. Les deux axes mondiaux sont donc **(0,−1,0)**, avec l'**accord d'orientation des profils LDCad**. Il faut éviter de les déclarer incompatibles sous prétexte que notre `find_connections` exige actuellement des axes de connexion **opposés** : cette convention interne doit traduire la **normale de réception** de la femelle avant de comparer au tenon, et non recopier le vecteur LDCad brut.

**Profil nominal :** F ronde rayon **6**, profondeur **20** ; M ronde rayon **6**, longueur **4** ; géométrie et sexe complémentaires, centre et axe exactement concordants. LDCad dispose donc des **métadonnées nécessaires pour reconnaître cette correspondance nominale**. **Nous avons vérifié les règles et les matrices, pas exécuté l'interface LDCad pour observer un « snap » effectif.**

### Trois niveaux de preuve (à ne pas confondre)

1. **Connexion nominale définie dans LDCad : OUI.** Site F (10,24,0), M R6×4, définitions externes authentiques et deux placements sans décalage.
2. **Connexion de la paire B3 reconnue par calcul de cette bibliothèque : OUI, nominalement.** Une paire F/M avec coordonnées exactes. **Mais le moteur BOLDÜNGO actuel renvoie toujours `find_connections = 0`**, faute de métadonnée de socket inférieur 30363 ; aucune validation du modèle complet.
3. **Compatibilité physique complète : NON CERTIFIÉE.** Les résultats M028–M029 (CONTACT de la paire entière ; signal COLLISION du tenon isolé sur une fin de trajectoire) ne sont ni effacés ni contournés. LDCad décrit un accrochage *éditeur*, pas la preuve d'absence de pénétration de matière, d'insertion, de tolérances ou de tenue.

## 5. Adaptation ciblée proposée, **NON APPLIQUÉE**

**Moteur existant seulement :**
- Ajouter une **source optionnelle de métadonnées de connexion LDCad**, distincte des maillages LDraw, pour la seule famille `30363.dat`, **versionnée/épinglée** à la révision externe `9b1131fb1991f8c0bfc072325e4e12f6271aba35`.
- Lire les seules directives `SNAP_CYL` strictement documentées, leur `gender`, `secs`, `pos`, `grid`, `ori`, `caps`, puis hériter correctement des sous-pièces à matrices d'identité. **Échec fermé** lorsque le fichier ou une option n'est pas reconnu. Pas de « connecteur » créé à partir de l'AABB.
- Traduire chaque femelle F en candidat `anti_stud` **métadonné**, avec le bon emplacement/axe sous 30363 et une profondeur distinguant **20, 14, 8, 4 LDU** ; conserver les deux vrais tenons supérieurs de M026.
- Confronter le mâle de `3004` issu de `p/stud.dat` aux seules femelles qui satisfont **sexe, forme, rayon, profondeur, centre et orientation**. Rejeter le deuxième tenon hors des huit sites de 30363 ; ne pas imposer deux tenons engagés pour reconnaître le match nominal simple.
- **Collision :** les paires contenant 30363 doivent garder les signaux `COLLISION` du moteur ; la présence d'un `SNAP_CYL` **NE TRANSFORME PAS** une collision en connexion physiquement valide. Séparer `nominal_snap_match` de `physical_clearance_validated` et `support_stability_established`.
- Tests futurs : correspondance unique du site (10,24,0) B3 ; 7 autres sites correctement transformés ; translation/rotation incorrectes refusées ; provenance manquante refusée ; condition de collision prioritaire ; régression des références 3004/3005 ; tests sur géométries LDraw originales séparés des métadonnées LDCad.

**Ce rapport propose une méthode. Aucune ligne de `library.py`, `assembly.py`, de tests ou de maillage n'est modifiée dans cette M030.**

## 6. Licence LDCad — contrôle **avant intégration**

**Auteur/source :** Roland Melkert, contributeurs de [LDCad Shadow Library](https://github.com/RolandMelkert/LDCadShadowLibrary), révision `9b1131fb1991f8c0bfc072325e4e12f6271aba35`. **Licence du dépôt :** [Creative Commons Attribution-ShareAlike 4.0 International](https://github.com/RolandMelkert/LDCadShadowLibrary/blob/9b1131fb1991f8c0bfc072325e4e12f6271aba35/LICENSE.md), également annoncée dans le [README](https://github.com/RolandMelkert/LDCadShadowLibrary/blob/9b1131fb1991f8c0bfc072325e4e12f6271aba35/README.md) et dans les en-têtes des fichiers de métadonnées.

- La **lecture, comparaison et citation des informations techniques** est distincte de leur **copie/incorporation dans un logiciel distribué**.
- Si les métadonnées LDCad originales, ou une adaptation protégée de ces données, sont redistribuées : conserver crédit auteur, référence source, licence et indication des modifications ; **les adaptations partagées sont soumises au partage à l'identique (SA)**, selon les conditions de CC BY-SA 4.0. Il faut examiner la compatibilité avec la licence et le mode de distribution du projet BOLDÜNGO **avant** d'intégrer/copier une bibliothèque de métadonnées.
- **Aucun fichier shadow LDCad n'a été copié dans le dépôt BOLDÜNGO**. Ce rapport se limite à des définitions techniques factuelles, des calculs et des liens de provenance. Les données restent externes jusqu'à une décision de licence et un test dédié.

## 7. Conclusion et décision de construction

**CONNEXION NOMINALE : OUI** — un véritable tenon `3004` se trouve exactement à l'emplacement d'une réception F `30363` publiée par LDCad, avec profils R6 complémentaires et axes cohérents. **Cela invalide l'idée selon laquelle le manque de connecteur dans notre moteur impliquait forcément un assemblage impossible.**

**Aucune conclusion d'absence de collision ou de stabilité physique n'en découle.** Les résultats M029 sur la matière restent à résoudre séparément avant de déclarer un appui porteur certifié.

**Prochaine décision proposée à Grand-père :** autoriser une mission ultérieure, uniquement dédiée à l'interprétation sûre et respectueuse de la licence des métadonnées LDCad dans le moteur existant, avec **tests positifs/négatifs et priorité des collisions**, sans déplacement des pièces B3.

**M030 précédente : annulée dans l'état courant. M030 nouvelle : diagnostic documenté. PR #931 DRAFT, PR #941 inchangée.**
