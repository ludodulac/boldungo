# Boldüngo — passe de raisonnement architectural avant sérialisation

## But

La conversion Survey → Scene ne doit plus demander à l’IA de passer directement de la reconnaissance visuelle au JSON final. Une étape de raisonnement architectural explicite doit précéder toute sérialisation.

## 1. Compréhension de l’objet

Pour chaque objet certain/plausible du Survey :
- identifier sa nature architecturale ;
- retrouver le même objet dans toutes les vues pertinentes ;
- distinguer les parties visibles, occultées et ambiguës ;
- identifier ses relations physiques avec bâtiment, sol, plateformes, escaliers et volumes voisins.

Pour un escalier : déterminer le sens de montée, l’extrémité basse, l’extrémité haute, la surface du bâtiment ou de la plateforme reçue à l’arrivée, et les indices visibles de marches, contremarches, murs latéraux et niveaux.

Pour le terrain : distinguer la vérité qualitative (par exemple « la rue monte vers l’arrière ») de son amplitude métrique. Une pente observée reste présente dans la Scene même si une ou deux altitudes du `GradeProfile` doivent rester `null`.

## 2. Hypothèses géométriques

Ne pas choisir immédiatement une coordonnée unique. Construire d’abord des intervalles/hypothèses compatibles avec :
- perspective et lignes de fuite ;
- coins et arêtes partagés ;
- alignements verticaux/horizontaux ;
- répétitions d’ouvertures et niveaux ;
- dimensions utilisateur connues ;
- mêmes objets vus sous plusieurs angles.

Les références usuelles d’objets architecturaux peuvent fournir uniquement des plages plausibles secondaires. Elles ne remplacent jamais les preuves de la maison photographiée.

Une amplitude de terrain ne doit pas être fabriquée depuis une pente simplement visible. Si les vues permettent de borner les niveaux, ils peuvent être `inferred` avec une confiance prudente ; sinon le profil reste partiellement métriquement inconnu sans perdre l’observation.

## 3. Résolution conjointe

Les objets liés physiquement sont résolus ensemble. Une relation `connects_to` certaine est une contrainte du système géométrique, pas une annotation à recopier après coup.

Exemple escalier → bâtiment : l’extrémité haute, le mur receveur, le niveau d’arrivée et la position du bâtiment doivent être compatibles simultanément. Il est interdit d’estimer l’escalier et le bâtiment séparément puis de déclarer la relation `resolved` si leurs métriques ne se touchent pas.

## 3.1 Continuité du profil architectural visible

**Règle canonique : `ARCHITECTURAL-UPPER-PROFILE-CONTINUITY`.**

Lorsqu'un même élément architectural de bordure visible — par exemple parapet, mur d'escalier, garde-corps maçonné plein, rampe pleine, bordure ou acrotère — traverse une transition de pente, deux propriétés doivent être préservées et validées séparément :

- continuité de masse ;
- continuité du profil supérieur visible.

Invariant explicite :

`MASS_CONTINUITY != UPPER_PROFILE_CONTINUITY`

Une géométrie peut donc être matériellement continue tout en étant visuellement fausse si son sommet introduit une troncature, une encoche, une terminaison anticipée ou un décrochement local sans preuve.

Si les photographies permettent de lire un même élément comme :

`segment incliné → jonction → segment horizontal`

la traduction constructive doit préserver cette topologie de silhouette à travers la jonction. Le changement de pente est autorisé ; l'invention d'une nouvelle rupture de profil ne l'est pas.

Cette règle ne fixe aucune métrique non observable. Les hauteurs, longueurs et quantifications LEGO exactes peuvent rester estimées ou inconnues. Ce qui est protégé est la continuité architecturale du profil et son changement de régime (incliné puis horizontal), pas une cote arbitraire.

## 3.2 Identité d'arête avant continuité de profil

**Règle canonique : `EDGE-IDENTITY-BEFORE-PROFILE-CONTINUITY`.**

Avant d'appliquer une contrainte de continuité, de prolongement ou de lissage à un profil architectural, Boldüngo doit d'abord établir que les segments appartiennent réellement au même élément architectural ou à une même chaîne de bordure démontrée.

Ordre obligatoire de raisonnement :

`EDGE_IDENTITY → MASS/PROFILE_CONTINUITY_CHECK → LEGO_TRANSLATION`

Ordre interdit :

`GEOMETRIC_PROXIMITY → PROFILE_CONTINUITY`

En particulier :

`COPLANAR + CONNECTED + HEIGHT_COMPATIBLE` n'implique pas `SAME_ARCHITECTURAL_EDGE`.

L'identité peut être soutenue par l'appartenance au même mur, parapet ou volume, une jonction physique réelle, la continuité multi-vue, l'ordre d'occultation, un changement de direction architecturalement explicable, les niveaux relatifs et la relation à la circulation, aux plateformes et aux volumes voisins.

Ne suffisent jamais seuls : proximité, coplanarité, contact, hauteur compatible, continuité matérielle ou possibilité de tracer une ligne continue.

Une règle de continuité ne doit jamais décider elle-même de l'identité des arêtes. Si l'identité n'est pas confirmée, la continuité correspondante reste non résolue et ne doit pas être matérialisée par la traduction LEGO.

## 4. Audit contradictoire

Avant sérialisation, rechercher activement les contradictions :
- relation dite résolue mais contact métrique absent ;
- ouverture hors de sa façade ;
- objets qui se chevauchent sans relation ;
- niveaux incompatibles entre vues ;
- échelle locale incohérente avec l’ancre utilisateur ;
- hypothèse sémantique incompatible avec la géométrie ;
- pente de terrain certaine supprimée parce que son amplitude n’est pas mesurable ;
- amplitude de terrain inventée pour rendre le modèle LEGO.

Toute contradiction doit être corrigée par une nouvelle résolution des seules valeurs `inferred`, ou laissée `unresolved` si elle n’est pas défendable. Ne jamais faire passer le validateur par snapping arbitraire.

## 5. Sérialisation seulement en dernier

Le JSON ArchitecturalScene v0.2 est la sortie d’un raisonnement déjà cohérent. Les champs `geometry_status:"resolved"` et `semantic_anchor_volume_id` ne sont autorisés qu’après vérification numérique finale des contraintes backend.

Les profils de terrain suivent la même règle : préserver d’abord la façade, la direction qualitative, la source et les preuves ; sérialiser `start_elevation`/`end_elevation` à `null` quand les valeurs métriques ne sont pas défendables. Le renderer LEGO attend une amplitude métrique au lieu de l’inventer.

## 6. Une photo vs plusieurs photos

Avec une seule photo, conserver davantage d’intervalles, de faibles confiances et d’inconnues. Avec plusieurs photos, utiliser les vues comme contraintes croisées pour réduire progressivement ces intervalles. Les vues ne sont pas des estimations indépendantes : elles décrivent une seule scène physique commune.
