# BOLDÜNGO — M041 : liaison de charpente, maillage réel et montage séquencé

**Branche indépendante :** `feat/boldungo-parallel-033-charpente`, PR #943 maintenue **DRAFT**. Reprise du HEAD M037 `2f005abd3f3b3c83b1674342e195ff09696cf007`. Le modèle de référence `missions/B3/generated/GUIDED004-B3-1904.ldr` conserve ses **1 904 pièces** et son blob Git `288c60fde76918128d8b955f78ebfa9afc2dfe8e`.

## Pièces et source de géométrie
- **Ajout seul** : vraie `3004.dat` à `(440, -792, 50)`. Le `M041-GUIDED004-APPUI-ORDONNE.ldr` reprend exactement les transformations B3 de `wall-000699`, `gable-000001`, `gable-000006`, `roof-000025`, `roof-000048`. Aucun de ces originaux n'est déplacé.
- L'audit autonome `audit_041.py` charge **37 véritables fichiers DAT LDraw** (pièces, subparts et primitives, dépôt public `pybricks/ldraw` au commit figé `c43ed06a128a10ed65675166bf42eb6fd608b9b0`). Il déroule récursivement les matrices LDraw et triangle les faces 3/4 ; les simples arêtes ne sont pas comptées comme matière. Le support seul contient **172 faces triangulées**.
- Fenêtre de voisinage : **48 pièces originales** évaluées (dont la face locale du mur et les deux pentes étudiées) ; **6 enveloppes de maillage** présentent un contact potentiel avec l'enveloppe du support : `gable-000001`, `gable-000006`, `roof-000024`, `roof-000025`, `roof-000047`, `roof-000048`.

## Contacts et géométrie
- **Connexions nominales confirmées par audit M037 :** mur `699` → pignon `001` : 4 tenons ; pignon → support `3004` : 2 tenons ; support → `30363 roof-000048` : 2 sites LDCad, profondeurs 8 et 14 LDU. Il s'agit de correspondances de connecteurs, pas d'essais de résistance.
- **Test M041 de traversées surfaciques :** zéro croisement strict d'arête de triangle à face triangulaire dans les six paires locales à l'emplacement final. Ce résultat vérifie une propriété du maillage réellement lu, mais ne prouve pas l'absence de pénétration volumique en cas de faces coplanaires, de volumes entièrement inclus, d'erreurs de surface ou d'une tolérance de fabrication. Une collision pleinement certifiée demanderait un test solide/volumique et un balayage continu.

## Séquence d'introduction (prélèvements tous les 8 LDU)
- **Mur → pignon → support (sans toiture déjà installée)** : zéro traversée surfacique détectée aux sept positions verticales échantillonnées de -48 à 0 LDU.
- **Introduire le support sous une toiture déjà en place** : **BLOQUÉ**. Le maillage de `roof-000048` coupe celui de la `3004` pour les translations verticales intermédiaires de -40 à -8 LDU ; jusqu'à 150 paires de triangles pénétrantes signalées par position (plafond de comptage).
- **Puis installer `roof-000048` après le support**, les autres pentes étant encore absentes : zéro traversée surfacique aux sept positions verticales échantillonnées. Cette variante de séquence ne prouve pas qu'on puisse monter ou démonter le toit complet 22° avec tous ses voisins déjà présents.

## Verdict et limites
**Premier raccord nominal avec contrôle de triangles LDraw : OUI.** La séquence locale *mur, pignon, support, toiture* est moins conflictuelle que l'insertion du support avec toiture déjà posée. **Assemblage physiquement certifié : NON.** Ni trajectoire continue libre de collision, ni géométrie volumique solide et tolérances, ni insertion des tenons LDCad, ni résistance, ni verrouillage réel de la pente ≈22° ne sont démontrés.

**À faire pour M045 :** volume solide / rayons de connexion / tolérances, trajectoire continue d'assemblage de `roof-000048` avec les deux pentes latérales et les pignons, puis reprise d'efforts jusqu'au mur fondé. Aucun moteur partagé, modèle B3 ou fichier d'une autre équipe n'est modifié. Aucune fusion et aucune publication.
