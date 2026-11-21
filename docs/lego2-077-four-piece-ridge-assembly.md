# LEGO2-077 — Assemblage virtuel complet des quatre éléments au faîtage

## Pièces et portée

L'étude reprend **une seule** alternative : le potelet central LEGO **3005 (1×1)**, la couverture transversale **26603 (2×3)**, le versant négatif **30363** et le versant positif **30363**. Pour l'orientation perpendiculaire déjà modélisée, la même étude porte sur la couverture **87079 (2×4)** ; sa sous-face demeure non validée. Aucun autre assemblage alternatif n'est créé.

La vérification `review_simultaneous_ridge_assembly` dépend uniquement des sorties existantes 065–076. Elle exige une colonne centrale appuyée nominalement sur le mur jusqu'à **z=0**, ses connexions locales `VALID` au sens restreint du contrôleur, **deux versants distincts** identifiés et **aucun cylindre de tenon partagé** entre le potelet et un versant. z=0 est seulement une cote architecturale, pas une fondation certifiée.

## Assemblage virtuel simultané

Les **quatre pièces** sont instanciées exactement dans leurs positions de référence. Si une bibliothèque LDraw compatible est fournie, les **six paires simultanées** sont étudiées avec `_pair()`, le moteur du projet :

1. Potelet ↔ couverture ;
2. Potelet ↔ versant négatif ;
3. Potelet ↔ versant positif ;
4. Couverture ↔ versant négatif ;
5. Couverture ↔ versant positif ;
6. Versant négatif ↔ versant positif.

Chaque relation `COLLISION` déclenche **REVIEW_REQUIRED**, sauf si la géométrie officielle manque ou si le budget a empêché une vérification complète : ces dernières situations restent **UNKNOWN**. Une collision LDraw peut aussi provenir de l'interférence normale des tenons et des tubes ; on ne la déclare jamais automatiquement impossible.

Le dépôt ne contient qu'une **petite bibliothèque LDraw de tests** (sans maillage officiel complet 26603/30363). Cette bibliothèque ne permet **pas** de conclure sur le montage réel. Les contrôles physiques complets devront donc être exécutés uniquement lorsqu'une bibliothèque officielle suffisamment complète sera présente.

## Séquence d'insertion

Deux versants et le potelet restent immobiles dans les coordonnées canoniques. Une **tuile expérimentale non enregistrée** est abaissée verticalement depuis des hauteurs `+3,+2,+1,0` plaques au-dessus de sa position, avec trois confrontations par hauteur (tuile/potelet et tuile/deux versants). Les résultats à la hauteur zéro réutilisent les couples simultanés déjà contrôlés.

Il s'agit de **quatre positions discrètes**, pas d'une trajectoire continue. L'insertion des deux pentes et la mise en place de la colonne porteuse ne sont pas simulées et restent **UNKNOWN**. L'absence de collision dans ces échantillons ne prouve pas une insertion physiquement réalisable.

## Décision

- **INVALID** est réservé à une contradiction démontrée du placement actuel : deux tenons coïncidents ou altitude du potelet incompatible avec le plan d'emboîtement.
- **REVIEW_REQUIRED** signifie que les maillages nécessitent un examen de leur interférence, non une incompatibilité définitivement prouvée.
- **UNKNOWN** signifie que l'assemblage multi-pièces, la sous-face de la couverture, l'emboîtement simultané et/ou l'insertion ne sont pas démontrés.
- Aucun verdict d'assemblage **VALID** n'est émis : le moteur LDraw n'évalue pas le serrage réel, les déformations des tenons, les tolérances, la rigidité, le flambement ou la charge.

La seule preuve positive conservée concerne les **liaisons nominales de la colonne 1×1** déjà documentées par 070/071. Le fait que la colonne évite les quatre tenons superposés de l'alternative 3002 (075) ne démontre pas à lui seul l'emboîtement sur trois pièces sous la couverture.

Les essais comportent deux orientations, plusieurs positions de bâtiment, les cas monopente/absence de versant, le mur flottant, le budget de maillage, les collisions forcées, les rapports LDraw incomplets et l'immuabilité du modèle.

**GUIDED-004 : 1 890 pièces inchangées ; aucune pente, aucun versant, aucun appui modifié.** `main` et la PR #881 inchangées.

**STATUT FINAL : NOT_CERTIFIED.**
