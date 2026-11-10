# BOLDÜNGO — Mission 031 — intégration LDCad ciblée `30363`

**Statut initial : intégration optionnelle préparée, contrôles CI à mesurer avant de conclure PASS.**

## 1. Source externe, licence et provenance
- **LDCadShadowLibrary** (Roland Melkert et contributeurs), révision exacte : `9b1131fb1991f8c0bfc072325e4e12f6271aba35`.
- Source : https://github.com/RolandMelkert/LDCadShadowLibrary/tree/9b1131fb1991f8c0bfc072325e4e12f6271aba35
- Licence : **CC BY-SA 4.0**, https://creativecommons.org/licenses/by-sa/4.0/ . Attribution à Roland Melkert et aux contributeurs. Les fichiers externes restent téléchargés **uniquement au moment des tests** dans un répertoire temporaire, **jamais recopiés dans BOLDÜNGO**.
- Si ces métadonnées, ou des adaptations substantielles, sont distribuées ultérieurement, attribution, indication des modifications et conditions ShareAlike doivent être vérifiées pour la distribution concernée. Leur utilisation technique **ne transfère pas** automatiquement une licence à la maison ou au moteur ; avis juridique spécifique si diffusion prévue.
- La lecture ciblée n'intervient que lorsque `LDrawLibrary(ldraw_root, ldcad_shadow_root=external_path)` reçoit un chemin explicite. Sans cette option, comportement M026 **identique**.

## 2. Source de géométrie d'origine
- `pybricks/ldraw@c43ed06a128a10ed65675166bf42eb6fd608b9b0` ; géométrie `30363.dat`, `s/30363s01.dat`, `3004.dat`, `s/3004s01.dat`, `p/stud.dat`.
- Pente : **2 tenons supérieurs** vérifiés en M026, inchangés. Métadonnées tierces 30363 : **4 rangées × 2 colonnes = 8 réceptions femelles**, section ronde rayon 6 LDU, profondeur variable **20,14,8,4 LDU**.
- La lecture est **strictement bornée à 30363**. Elle refuse les champs, profils, orientations non orthonormales, grilles, rangées et combinaisons inattendues (échec fermé, sans réceptions inventées). Normalisation des axes : source LDCad —Y ; normale de réception de notre moteur +Y.

## 3. Une seule paire du modèle B3
- Original non modifié : `missions/B3/generated/GUIDED004-B3-1904.ldr` — `roof-000048` 30363, origine (470,−816,60), orientation `[0,0,1;0,1,0;−1,0,0]` ; `gable-000006` 3004, origine (480,−792,50), rotation identité.
- Réception F locale `(+10,24,0)` → monde `(470,−792,50)`; tenon M de la 3004 local `(−10,0,0)` → **même point**. Second tenon `(490,−792,50)` sans correspondance.
- **Test positif attendu : 1 connexion nominale**, pas une fixation physique certifiée. Déplacement/rotation erronés : **aucune** correspondance.
- Aucun chargement des 408 pentes dans ce test, aucun changement de maillage.

## 4. Statuts séparés obligatoires
1. **CONNEXION NOMINALE RECONNUE :** renseignée d'après métadonnées, position et orientation — hors certification de matière.
2. **ABSENCE DE COLLISION VALIDÉE :** **NON CERTIFIÉE**. Toute collision du moteur pour la pente 30363 reste bloquante, indépendamment de `SNAP_CYL`.
3. **INSERTION VALIDÉE :** **NON CERTIFIÉE** (aucune trajectoire complète de pièces).
4. **STABILITÉ VALIDÉE :** **NON CERTIFIÉE** (aucune preuve mécanique).

## Résultats mesurés — CAMPAGNE UNIQUE GITHUB ACTIONS

**SUCCESS — 32 tests réussis en 0,32 seconde**, un seul job actif `recognize-ldcad-30363-031`.

- Exécution : https://github.com/ludodulac/boldungo/actions/runs/42834410081
- Artefact : `BOLDUNGO-M031-LDCAD-30363-NOMINAL-ONLY` (journal de tests).
- **23 fichiers de géométrie LDraw** réellement téléchargés dans le runner. **4 fichiers shadow LDCad** distincts effectivement lus depuis les URL figées : `parts/s/30363s01.dat`, `parts/3004.dat`, `parts/s/3004s01.dat`, `p/stud.dat`. Ces fichiers ne sont pas ajoutés au dépôt.
- **8/8 logements inférieurs `30363` reconnus** ; quatre profondeurs **20, 14, 8, 4** préservées, 2 points par rangée ; les **2 tenons supérieurs M026** conservés.
- **Paire B3 : 1 connexion nominale reconnue**, `anti_stud:stud`, position mondiale **(470,−792,50)** ; le deuxième tenon à (490,−792,50) ne correspond à aucun site. Le test instancie **seulement deux pièces** à leurs transformations B3 déjà vérifiées, sans modifier le fichier B3 ni instancier le reste de la maison.
- **Position incorrecte : rejetée** (translation erronée et rotation de l'axe). Sources shadow manquantes, méta incorrecte, grille incohérente, profil de profondeur incorrect, orientation non orthonormale : **échec fermé** sans logement inférieur fictif.
- **Collision bloquante : PASS** — test avec moteur renvoyant `COLLISION` : la présence du snap LDCad laisse l'assemblage **invalide**, collision `slope_30363_mesh_intersection_review_required` maintenue. Il s'agit d'un garde-fou logiciel, **pas** d'une certification de pénétration matérielle réelle.
- **3004/3005 et tests M026 existants : PASS**. Anciens audits globaux M020–M029 **non relancés**.

Les correspondances retournées avec origine LDCad sont explicitement marquées `nominal_connection_recognized=True`, `absence_of_collision_validated=False`, `insertion_validated=False`, `stability_validated=False`. L'absence d'alertes du seul petit test de connexion **ne constitue pas** une certification physique.

## 5. Tests et absence de contournement
- Une campagne GitHub Actions ciblée **exécutée et terminée : 32 PASS**, regroupant tests M031 positifs/négatifs, huit sites et profondeurs, transformations, origine externe manquante/invalide, collisions bloquantes, tests M026 et régressions 3004/3005 existantes.
- Les journaux GitHub ont été consultés. **32 PASS** valident les comportements logiciels ciblés, **sans** preuve de compatibilité matérielle complète.
- PR #931 reste en DRAFT, PR #941 inchangée ; aucune modification du fichier B3, ni du site, ni des photographies.
