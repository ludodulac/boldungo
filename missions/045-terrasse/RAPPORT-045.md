# M045 — Grand-père BOLDÜNGO · CONSTRUCTION TERRASSE

**HEAD de départ :** `fca15489b56e434b386646716e61e300d127ed29`, branche `feat/boldungo-parallel-035-terrasse`, PR #944 **DRAFT**.

**Périmètre :** variante M043 en lecture seule. Ni B3 (1 904 pièces), ni M035/M039/M043, ni moteur, ni toiture, ni fenêtres, ni escalier n'ont été édités.

## Diagnostic précis

Dans la zone terrasse bois M043, **48 pièces sont des éléments provisoires ou sans liaison nominale défendable** :
- **39 pièces de garde-corps (lisses/montants)** : ensemble incomplet, nombreuses lisses ou montants avec zéro contact tenon documenté ; le conserver tel quel laisse des barres suspendues devant le mur. Le retrait des 39 est **temporaire dans la copie M045** et ne constitue pas une restitution architecturale finale. Les garde-corps doivent être rebâtis ensuite sur de vrais ancrages.
- **4 pièces `EXPERIMENT-B2-DECK-*`** : deux poutres/renforts et deux plaques de couture d'essais antérieurs. Bien que certaines aient un contact nominal avec une planche, elles n'ont pas de rôle porteur démontré et leur conservation crée des excroissances inutiles.
- **5 plaques de `hidden-cross`** : aucune attache tenon nominale reconnue dans le modèle rectangulaire de la terrasse ; retirées dans la seule variante. **Quatre autres plaques cachées avec recouvrements nominaux sont conservées.**

**Décisions :** 48 retraits ciblés, 29 briques des trois poteaux existants repositionnées sur la grille LEGO pour éviter leur terminaison dans le vide et **une seule 3005 ajoutée** en tête du poteau Est. Aucune grosse structure inventée.

La terrasse principale et les **3 planches jointives du retour** sont conservées : retirer le revêtement sous prétexte d’absence de certification supprimerait arbitrairement la surface architecturale. Le **Y Technic de M039 est conservé à l'identique** (deux bras 32524 et trois broches 6558).

## Limites et résultats

La nouvelle géométrie offre des contacts nominaux poteau → planche sur chacun des trois appuis et le réseau des fûts reste jointif. Les positions des poteaux sont **hypothétiques, arrondies à la grille** et non une nouvelle mesure de la maison. La différence bois/béton reste 24 LDU (hypothèse M039).

Comparaison AABB des modèles *maison entière* M043 → M045 : **${before.length} → ${after.length} paires**, **zéro nouvelle superposition**. Les collisions héritées ne sont pas masquées ; les maillages Technic inclinés ne sont pas intégralement testés.

**Zones ambiguës restant à traiter une autre fois :** deux planches du retour contiguës sans liaison inférieure indépendante prouvée ; quelques planches adjacentes non reliées par connecteurs physiques ; garde-corps supprimé provisoirement en attendant un calepinage sûr ; ancrage du Y au sol, insertions et résistance mécanique non certifiés. Le modèle n'est **pas** prêt à monter ni à utiliser comme terrasse réelle.

**Livrables :** `PROTO-045-TERRASSE-BOIS-NETTOYEE.ldr`, `GUIDED004-B3-EXPERIMENTAL-M045.ldr`, `AUDIT-045.json`, `BOM-045.json`, `APERCU-045.svg`, `VERIFIER-045.py`. PR DRAFT ; aucune fusion ni publication.
