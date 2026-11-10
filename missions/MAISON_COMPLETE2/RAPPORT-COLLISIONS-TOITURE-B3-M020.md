# BOLDÜNGO — Mission 020 — statut de l'exécution ciblée

HEAD vérifié avant préparation : `c6f5fb71dbf3619f98a1b81e360ef1c31ca30e78`. PR #931 maintenue en DRAFT ; PR #941 non modifiée.

## Préparation
- Le modèle B3 est **inchangé** : `missions/B3/generated/GUIDED004-B3-1904.ldr`.
- **1 904** placements, dont **408 `30363.dat`**, comptés lors de la mission 019.
- Le script de contrôle réutilise `LDrawLibrary`, `candidate_pairs`, `check_collision` et `find_connections` du moteur existant.
- Le workflow existant `.github/workflows/lego2-b1-guided004-full-house.yml` propose l'option manuelle `mission = M020`. **Un seul job M020** s'exécute pour cette option ; le job B1 historique n'est pas exécuté.
- La bibliothèque pybricks/ldraw épinglée `c43ed06a128a10ed65675166bf42eb6fd608b9b0` est téléchargée **dans le runner** depuis les 18 familles de pièces effectivement citées par B3, avec fermeture de dépendances, sans ajout de fichiers tiers au dépôt.
- Le diagnostic est borné à **60 couples de maillages** et **540 secondes** après initialisation, et sauvegarde un fichier JSON plus un rapport Markdown comme artefacts GitHub Actions.
- Les chevauchements de boîtes sont un préfiltre, les collisions de maillages ne sont jamais automatiquement assimilées à une collision matérielle physiquement interdite.

## État actuel : ACTION_REQUIRED — exécution non confirmée

Le connecteur GitHub disponible peut lire/écrire les fichiers et consulter les exécutions mais **ne dispose pas de commande permettant le déclenchement `workflow_dispatch`**. Cette préparation est enregistrée avec `[skip ci]` pour **ne pas déclencher la CI générale**. Aucun test M020 n'est prétendu exécuté.

Pour lancer l'unique campagne : dans GitHub → Actions → **LEGO2 B-1 GUIDED-004 complete 1901-piece experimental house** → **Run workflow** → sélectionner la branche `feat/lego2-b1-guided004-full-house-experiment`, option `mission: M020` → Run workflow **une seule fois**.

Lien : https://github.com/ludodulac/boldungo/actions/workflows/lego2-b1-guided004-full-house.yml

Après le lancement, récupérer l'artefact `BOLDUNGO-M020-B3-408-REAL-LDRAW-ROOF-NOT-CERTIFIED`. Le **véritable** résultat sera dans `RAPPORT-MISSION-020.md` et `B3-408-ROOF-MESH-AUDIT.json` de l'artefact, et **n'a pas été inventé ici**.

## Contrôles non encore accomplis
- Téléchargement LDraw GitHub Actions : **NON EXÉCUTÉ**.
- Maillage `30363` chargé dans le job M020 : **NON DÉMONTRÉ**.
- Pièces de toiture contrôlées par maillage : **0/408 prouvée**.
- Couples testés par maillage M020 : **0 prouvé**.
- Collisions matérielles interdites : **NON DÉMONTRÉ** (et non « zéro collision »).
- Constructibilité, insertion, stabilité : **NON CERTIFIÉES**.
