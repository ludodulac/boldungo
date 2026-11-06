# BOLDÜNGO — MAISON COMPLÈTE-1 : le défaut global de toiture est identifié

Source : `missions/B3/generated/GUIDED004-B3-1904.ldr` (1 904 véritables placements de briques), PR #931 DRAFT, commit de départ `dd3d4e360eba2fefbadbde59e6fe34030215e1fd`.

**Contrôle exact des coordonnées nominales** de la pièce LEGO/LDraw `30363.dat`. Son sous-modèle officiel épinglé `s/30363s01.dat` contient deux tenons supérieurs (`x=±10,y=0,z=0`) et la géométrie du dessous permet l'examen des deux cavités à (`x=±10,y=24,z=0`). Matrices de rotation et centres de tenons des autres briques repris du fichier LDraw existant.

| Mesure | Nombre |
|---|---:|
| Pentes 30363 | **408** |
| Deux cavités nominales face à des tenons | **22** |
| Une cavité nominale face à un tenon | **17** |
| **Aucun tenon nominal sous les deux cavités examinées** | **369** |
| Raccordements directs pente→pente au niveau des tenons/cavités de ces pièces | **0** |

**Conclusion mesurée : les 408 pièces ne constituent pas une toiture assemblable démontrée.** Les rangées espacées de 60 LDU horizontalement et 24 LDU verticalement ne se relient pas directement par les deux connecteurs nominatifs étudiés. Les 369 pièces sans ces appuis ne sont pas nécessairement entièrement dépourvues d'autres contacts : les maillages de tout le toit, les contacts spéciaux et les possibilités d'insertion n'ont **pas** été vérifiés.

Le cas `roof-000223 ↔ wall-000719` est retrouvé comme témoin positif, cohérent avec la preuve locale antérieure TOITURE-7. La preuve locale ne vaut pas validation de l'ensemble.

Résultat détaillé par chacune des 408 pièces : `TOITURE-CONTACTS-NOMINAUX.json`. Reproductibilité : `node scripts/audit_guided004_roof_nominal.mjs`.

## Décision de construction pour progresser rapidement

**Arrêter les rustines ponctuelles sous les pentes 30363**. Reprendre en une seule variante la **toiture entière** du modèle B-3, bâtie sur un réseau de briques/plaques effectivement reliées aux murs et pignons ; accepter un aspect simplifié proche de la silhouette d'origine si nécessaire pour obtenir un premier prototype LEGO montable.

Cette variante devra être générée dans **un nouveau fichier distinct** et soumise à : (1) raccordements pièces réelles, (2) collisions de vrais maillages LDraw, (3) ordre d'insertion réaliste, (4) contrôle visuel, (5) essai LEGO physique pour confirmer la solidité. **Aucun toit corrigé n'est créé dans ce diagnostic** : il serait trompeur de déclarer réparé un modèle dont le principe de connexion est à reprendre.

Pas de changement au modèle B-3 original, à `main`, ni à la version publique.
