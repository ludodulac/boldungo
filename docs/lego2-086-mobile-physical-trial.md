# LEGO2-086 — Le prototype LEGO est désormais ouvrable directement sur téléphone

## Pourquoi

Les missions 083–085 ont livré un mini-kit de 30 pièces, 24 étapes de châssis, un rapport d'appuis et deux fichiers LDraw. Un logiciel LDraw/BrickLink Studio reste peu pratique sur téléphone Android. Cette mission produit **un unique fichier HTML autonome**, consultable sans application spécialisée, sans connexion Internet ni serveur.

**Fichier généré** : `prototype-30-pieces.html` dans l'artefact CI `LEGO2-086-mobile-prototype-30-pieces`.

## Fonctionnement

1. Sur GitHub, ouvrir la CI spécialisée de la PR, télécharger l'artefact ZIP, puis extraire le fichier HTML.
2. Ouvrir `prototype-30-pieces.html` sur le téléphone ou l'ordinateur dans son navigateur (par exemple Brave ou Chrome).
3. Faire glisser le doigt sur le modèle pour tourner la **représentation 3D simplifiée**, utiliser la molette pour zoomer.
4. Appuyer sur « Suivant » ou utiliser le curseur pour consulter **les 24 poses réelles du châssis, dans l'ordre vérifié** par la mission 084.
5. Cocher « Montrer les 6 pentes jaunes » **uniquement comme hypothèse visuelle** : elles n'ont **pas** de liaison approuvée au faîtage. Cette vue n'est pas une notice autorisant leur pose.
6. Après le véritable test physique des briques, noter les étapes instables, les manques d'emboîtement et les jonctions de pente impossibles ; ne pas forcer.

## Garanties et limites mesurées

- La source du HTML est le **modèle expérimental exact 083**, vérifié dans l'ordre de **084**. Pas de duplicata manuel d'inventaire ni de positions.
- **18 × 3005**, **6 × 3008**, **6 × 30363** : **30 pièces**, dont 24 à connexion nominale étudiée, 6 à raccordement non documenté.
- Les enveloppes affichées sont des **volumes explicatifs simplifiés**, **pas les vrais maillages LDraw**, ni une preuve que les pièces entrent sans déformation.
- Le code HTML contient ses données intégrées (JSON), son CSS et son JavaScript : **aucune bibliothèque distante**, aucune clé API, aucun compte et aucune dépendance de réseau.
- Le HTML ne nécessite pas de déploiement de `main` ni de démarrer le serveur BOLDÜNGO. Le téléchargement ZIP est un fichier d'essai privé au lecteur, **pas une fonctionnalité annoncée en production**.
- Les six pentes peuvent ne pas toucher l'ossature ou ne pas se rejoindre correctement. **Si le montage n'est pas naturel, conclure à l'échec du prototype de faîtage B**, ne pas utiliser un succès des 24 premières étapes pour masquer l'échec.
- La stabilité des quatre colonnes 1×1 sur une table reste une hypothèse ; **aucune baseplate n'est incluse** dans les 30 pièces. Si les pieds basculent, le test mécanique échoue sans qu'on puisse valider la structure.

## Suite constructive (sans tunnel)

Après retour du test physique ou visualisation d'un conflit manifeste, décider **dans une seule itération** si la technique B doit être **abandonnée ou reconstruite autour d'une connexion de pente documentée**. Ne pas refaire les missions 075–081, ne pas fermer de maillages, ne pas fusionner une toiture hypothétique dans GUIDED-004.

**GUIDED-004 reste exactement à 1 890 pièces ; main et PR #881 inchangées ; NOT_CERTIFIED.**
