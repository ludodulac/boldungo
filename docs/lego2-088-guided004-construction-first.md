# LEGO2-088 — Construire la toiture sur la VRAIE maison, sans demander de test à l'utilisateur

## Changement prioritaire demandé

**L'utilisateur ne souhaite pas réaliser de test physique maintenant.** BOLDÜNGO poursuit donc **automatiquement** la conception selon des règles vérifiables, en travaillant sur **l'intégralité des 1 890 pièces** de GUIDED-004, pas un assemblage isolé de 3 ou 30 pièces.

Le modèle source est généré par **le véritable exporteur existant** `scripts/export_guided004_lego.py`. Il reste absolument intact : chaque proposition est dérivée dans une **copie expérimentale différente**, et le SHA-256 du fichier canonique est revérifié à la fin.

## Livrable d'ingénierie, pas un nouvel audit de maillages

`construct_rule_based_roof_experiment_088(model)` :

1. Lit toutes les pentes de toiture 30363 de la maison et extrait leurs **vraies deux coordonnées de tenons supérieurs** à travers le module 034 déjà accepté.
2. Regroupe les rangées par hauteur (plaques), direction, orientation et deux cellules longitudinales. Cette méthode fonctionne à d'autres tailles de maison et aux deux directions de faîtage.
3. Apparie uniquement une pente **négative** avec une pente **positive**, sur quatre tenons distincts.
4. Si l'écart transverse est d'un ou deux tenons, construit automatiquement une **brique centrale 3003 (2×2) ou 3002 (2×3)** correctement orientée, selon l'expérience 087. Les autres rangées ne sont PAS inventées.
5. Bloque les positions déjà occupées par une pièce orthogonale existante. Un ancien capuchon de faîtage ne peut être remplacé dans l'expérience que lorsque son empreinte correspond **exactement** au nouveau montage ; toute configuration partiellement superposée est refusée.
6. Empêche de revendiquer une paire de pentes deux fois, de créer deux briques centrales qui s'interpénètrent, ou d'insérer un capuchon au mauvais niveau.
7. Génère, si une proposition est admissible au niveau **stud projection**, une **copie expérimentale** avec les nouvelles pièces et le retrait local des seuls capuchons équivalents. La liste des pièces résultante est mesurée automatiquement.
8. Produit des **critères de rejet explicites** pour les autres emplacements et interdit de proclamer que le toit et la maison sont physiquement assemblables.

Les validations historiques 060–087 ne sont **pas** relancées. Aucune tentative de fermeture des maillages LDraw et aucun « nouveau diagnostic » des anciennes 3 collisions.

## Pourquoi cette étape ne certifie toujours pas la maison

Le haut des pentes 30363 possède des tenons localisés, mais **la fixation de leur dessous à l'ossature/murs n'est pas documentée**, et les briques centrales 3003/3002 ne possèdent pas encore de preuve de serrage pour **cette** jonction. Le calcul nominal n'établit pas non plus le dégagement réel de toutes les pièces voisines, la séquence d'assemblage de toute la maison, la descente des charges ni les efforts mécaniques.

Le programme a donc une règle de sécurité **non contournable** :

`construction_status = BLOCKED_NOT_YET_BUILDABLE`

Si aucune proposition n'est recevable, il publie **la décision d'abandon de cette technique** et indique de passer à une autre architecture LEGO documentée, plutôt que de prolonger l'analyse du même faîtage.

**Cette mission ne sollicite aucun test physique à l'utilisateur.** Des vérifications physiques restent nécessaires pour un jour revendiquer une certification de résistance N6 ; elles ne sont pas une condition pour continuer à développer le logiciel et la conception.

## Fichiers exploitables

GitHub Actions spécialisée `LEGO2-088 actual full-house rule-based roof candidate` :

- `CONSTRUCTION-DECISION-088.json` : décompte exact des pentes de la VRAIE maison, nouveaux capuchons compatibles nominalement, conflits et raisons.
- `GUIDED-004-EXPERIMENTAL-NOT-CERTIFIED.json` : copie **uniquement si** des remplacements sont générables, jamais le modèle original.
- `EXPERIMENTAL-BOM-DELTA.json` : changements exacts de nomenclature, séparés du modèle initial.
- `LIRE-AVANT-CONSTRUCTION.txt` : avertissement clair que le fichier est une proposition d'ingénierie, non une notice constructible.

## Poursuite après résultat mesuré

- Si plusieurs connexions sont nominalement possibles : se consacrer **au véritable support de la sous-face des pentes jusqu'aux murs**, et à une technique de retenue LEGO qui possède des interfaces officiellement vérifiées.
- Si les capuchons entrent en conflit avec les pièces présentes : **changer de technique** (ossature interne documentée, sous-assemblages réorientés ou pièces réellement adaptées). Pas un 5e audit du même maillage.
- **Ne jamais éditer** le canonique `GUIDED-004`, les 1 890 pièces, `main` ou la PR principale #881 sans demande explicite de l'utilisateur.

**Résultat visé à terme : un modèle de la maison relié de la base jusqu'aux deux versants avec des joints justifiés, une nomenclature exacte et une notice de montage complète, sans attendre un test physique personnel à chaque mission.** Aucun N6 n'est attribué par une simulation seule.
