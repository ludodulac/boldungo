# BOLDÜNGO — MISSION 027 : CARTOGRAPHIE DES APPUIS DE TOITURE

## État initial : cartographie ciblée en cours de préparation

**Modèle inchangé :** `missions/B3/generated/GUIDED004-B3-1904.ldr`, blob `288c60fde76918128d8b955f78ebfa9afc2dfe8e`, contenant 1 904 pièces, dont 408 pentes `30363.dat`.

Le contrôle réutilise le moteur LDraw amélioré M026 et les vraies géométries épinglées `pybricks/ldraw@c43ed06a128a10ed65675166bf42eb6fd608b9b0`.

### Classification conservatrice

- **A :** connexion nominale portant sous la pente, démontrée par vrais connecteurs. Aucun logement inférieur `30363` n'étant connu, **aucun résultat A n'est présumé**.
- **B :** brique ordinaire avec tenon reconnu dans l'empreinte X/Z du maillage de la pente, proche du bord vertical inférieur de celle-ci : **appui seulement possible** ; emboîtement non démontré.
- **C :** aucun appui inférieur identifié par cette recherche ; ne prouve pas qu'aucun support réel existe.
- **D :** pièces proches, éventuellement autre pente sous-jacente, mais géométrie ou fixation trop incertaine pour la catégorie B.
- Les deux tenons **supérieurs** des pentes sont décomptés **séparément**, jamais confondus avec les supports inférieurs.

Le script produit pour chacune des 408 pentes une liste de pièces réelles candidates avec identifiants, références, coordonnées et transformations LDraw, ainsi qu'une paire proposée pour l'analyse ultérieure. **Pas de reprise du scan des 1 904 paires de collisions.**

## Résultats

**NON EXÉCUTÉ à ce stade** — les effectifs, catégories et la paire sélectionnée seront établis seulement après consultation de GitHub Actions. Le rapport complet sera dans l'artefact `BOLDUNGO-M027-B3-408-ROOF-SUPPORT-MAP-NOT-CERTIFIED` ; une copie sera enregistrée ici après vérification.

**Aucune pièce B3 ni aucune règle de collision modifiée. Constructibilité non certifiée.**
