# CAHIER DES CHARGES CANONIQUE — Boldüngo / BrickHouse

Statut : référence produit consolidée.  
Date de consolidation : 2026-09-19.

Ce document rassemble le **but produit**, le **parcours utilisateur attendu** et les **critères de réussite visibles**. Il ne remplace ni les contrats techniques, ni les ADR, ni les tests. Les détails d'implémentation restent dans les documents spécialisés indexés par `docs/_INDEX.md`.

## 1. Finalité du produit

Boldüngo doit permettre à une personne de fournir plusieurs photographies d'un bâtiment réel et d'obtenir une **maquette LEGO reconnaissable, architecturalement fidèle, physiquement constructible et accompagnée d'une notice pratique**.

Le produit ne cherche pas à « voxeliser » mécaniquement les pixels. Il doit comprendre l'architecture, conserver ce qui donne son identité au bâtiment, puis trouver une traduction LEGO explicite et honnête.

La chaîne cible est :

`PHOTOS → ArchitecturalSurvey → ArchitecturalScene → plan de représentation LEGO → BrickModel → validation physique → viewer / BOM / notice`.

## 2. Les photographies sont des sources primaires

Les photographies originales doivent rester accessibles comme preuves réanalysables, et non être remplacées par leur seule description textuelle.

Pour le benchmark `real-house-5`, les cinq JPEG canoniques sont conservés dans `frontend/benchmarks/real-house-5/` avec un `manifest.json`. Ils constituent le corpus source historique du benchmark.

Une nouvelle série de photographies ne doit **jamais** être interprétée comme une liste d'instructions du type « déplace cette terrasse » ou « ajoute ce mur ». Elle constitue de nouvelles **sources d'observation**.

Le système doit pouvoir confronter :

`ANCIENS PIXELS + NOUVEAUX PIXELS → compréhension multivue révisée`.

Il doit ensuite seulement décider quelles observations méritent d'enrichir ou de corriger le Survey.

Le parcours produit nominal doit pouvoir fonctionner à partir d'un petit ensemble de vues suffisamment informatives, typiquement environ cinq photographies d'un bâtiment. Des vues supplémentaires peuvent améliorer ou lever les incertitudes de la reconstruction, mais elles ne doivent pas devenir une condition implicite de réussite. Dans les benchmarks, des photographies supplémentaires peuvent constituer une vérité de contrôle privée réservée à l'évaluation d'une reconstruction produite exclusivement depuis le sous-ensemble nominal ; elles ne doivent jamais être accessibles au système candidat pendant cette reconstruction.

## 3. Réanalyse multivue

L'analyse doit distinguer explicitement :

- **OBSERVÉ** : visible dans une source ;
- **CONFIRMÉ MULTIVUE** : même fait soutenu par plusieurs vues ou identités recoupées ;
- **DÉDUIT / INFÉRÉ** : conclusion cohérente mais non directement observée ;
- **MESURÉ / ESTIMÉ MÉTRIQUEMENT** : information géométrique avec provenance propre ;
- **LEGO-CONSTRUCTIBLE** : représentation dont les pièces, contacts, connexions et supports sont suffisamment établis.

Ces catégories ne sont jamais interchangeables.

Plus de photos peuvent résoudre une identité, une occultation, une connexion architecturale ou une topologie sans fournir aucune nouvelle dimension. **Une certitude topologique ne doit pas devenir artificiellement une certitude métrique.**

Une vue nouvelle peut également conduire à relire correctement une ancienne vue. Le système doit préserver cette provenance croisée.

## 4. Survey : vérité observée et sémantique

`ArchitecturalSurvey` est l'autorité de l'inventaire observé, des identités, des certitudes et des relations sémantiques.

Il doit pouvoir conserver honnêtement les vérités qualitatives importantes même lorsque leurs coordonnées, dimensions, quantités ou traces exactes sont inconnues.

Exemples : existence d'un poteau sans nombre fiable ; présence d'un contreventement sans coordonnées ; parois accompagnant un escalier sans hauteur mesurée ; ouverture identifiée comme porte après confirmation multivue.

Si le contrat Survey ne possède pas encore le vocabulaire permettant d'exprimer une vérité observée, cette limite doit être enregistrée comme **dette contractuelle explicite**. Il est interdit de contourner le problème avec une clé locale opaque ou une fausse géométrie.

## 5. Scene : vérité géométrique

`ArchitecturalScene` traduit les vérités du Survey en une reconstruction spatiale cohérente.

Une primitive certaine du Survey ne doit pas disparaître simplement parce que sa métrique est difficile. Sa géométrie peut rester non résolue.

La Scene ne doit pas inventer un volume fermé lorsque les photos prouvent seulement une surface, des murs ou un espace partiellement visible. Elle ne doit pas créer des supports métriques pour matérialiser une structure seulement observée qualitativement.

Les corrections doivent viser la **première frontière responsable** de la perte de vérité et non compenser un défaut en aval.

## 6. Fidélité architecturale perceptive

Le résultat doit être reconnaissable par un humain comme le bâtiment source.

La fidélité ne signifie pas reproduire chaque centimètre. Une bonne traduction LEGO peut simplifier la géométrie tout en préservant les caractéristiques qui donnent son identité au bâtiment.

Priorités visuelles :

1. silhouette et proportions générales ;
2. volumes et niveaux ;
3. toiture, pignons, débords et cheminée ;
4. rythme, identité et position relative des portes et fenêtres ;
5. structures extérieures caractéristiques : escaliers, paliers, terrasses, garde-corps, porches ;
6. reliefs architecturaux significatifs : retraits, encadrements, corniches, appuis, rives ;
7. éléments secondaires observés lorsque le format et le catalogue le permettent : gouttières, descentes, luminaires, conduites, végétation ou décor.

Le résultat recherché est une **interprétation LEGO architecturale fidèle**, pas une masse de briques issue d'une discrétisation aveugle.

Le niveau de détail dépend du format physique et du profil de fidélité ; lorsqu'un détail important ne peut pas être conservé à l'échelle choisie, le produit doit signaler le compromis plutôt que le supprimer silencieusement.

## 7. Traduction LEGO

Les contraintes LEGO ne modifient jamais silencieusement la vérité architecturale.

Le moteur doit distinguer :

- représentation fidèle ;
- approximation LEGO explicite ;
- élément architectural conservé mais non encore matérialisable ;
- `fidelity_issue` ;
- impossibilité physique ou connectivité non certifiée.

Un élément visuellement bien placé n'est pas nécessairement constructible. **Proximité ≠ contact ≠ connexion ≠ support stable.**

L'ordre de travail reste :

`vérité spatiale → ancres LEGO → résolution des empreintes/conflits → remplissage → détails → validation physique → instructions`.

## 8. Notice

La notice est une sortie du modèle constructif, pas un moyen de masquer ses défauts.

Elle doit être majoritairement graphique : grandes vues de construction, pièces nouvelles clairement identifiées, quantités, progression visuelle et très peu de texte.

Elle ne doit jamais inventer un geste de connexion ou de support que le modèle physique n'a pas établi.

Une dette locale de constructibilité peut bloquer seulement les étapes concernées sans empêcher la poursuite des parties déjà établies.

## 9. Boucle de contrôle humain

Les tests techniques verts ne suffisent pas.

À des checkpoints bornés, le système doit produire des vues inspectables de la **maison entière**, idéalement avec des cadrages stables (perspective, avant, arrière, gauche, droite), afin de comparer :

`photos sources ↔ Scene ↔ modèle LEGO`.

Le contrôle humain doit porter d'abord sur les grandes divergences perceptives, avant les détails décoratifs.

Une amélioration interne n'est considérée comme un progrès produit que si elle préserve les contrats et améliore réellement ou protège la vérité visible/constructive.

## 10. Benchmark réel et nouvelles photographies

Le benchmark `real-house-5` sert de cas réel de validation.

Les nouvelles photographies d'un même bâtiment doivent suivre le protocole suivant :

1. les enregistrer comme sources avec provenance ;
2. ne pas corriger directement la Scene à partir d'elles ;
3. confronter anciennes et nouvelles vues ;
4. produire des observations multivues ;
5. enrichir/corriger le Survey seulement pour les vérités suffisamment soutenues ;
6. conserver les métriques inconnues ;
7. propager ensuite Survey → Scene ;
8. produire de nouveaux rendus comparables ;
9. seulement ensuite réviser la traduction LEGO ;
10. valider physiquement avant la notice.

Le benchmark doit donc mesurer la capacité de Boldüngo à **apprendre davantage des pixels sans halluciner davantage de géométrie**.

## 11. Provenance et histoire du benchmark

La provenance complète doit être conservée à partir de maintenant.

Pour `real-house-5`, les cinq JPEG originaux et le Survey accepté sont présents. Des artefacts structurés historiques existent également. En revanche, l'ancien PDF de handoff et l'identité exacte du JSON historiquement extrait de ce PDF ne sont pas établis dans le dépôt actuel.

Cette rupture historique ne doit pas être masquée. Elle n'empêche pas la réanalyse, car les pixels sources canoniques ont survécu.

Toute nouvelle campagne photo doit éviter de recréer cette rupture : source → observation → Survey → Scene → LEGO doit rester traçable.

## 12. Gestion documentaire

Ce fichier est le **cahier des charges produit canonique**.

Ne pas recopier ses exigences dans plusieurs documents concurrents. Les documents spécialisés détaillent le « comment » :

- `PROJECT_PRINCIPLES.md` : constitution courte et invariants ;
- `docs/DECISIONS.md` : décisions d'architecture et motivations ;
- `docs/ARCHITECTURAL_SURVEY_V01.md` : contrat Survey ;
- `docs/ARCHITECTURAL_SCENE_V02.md` : contrat Scene ;
- `docs/ARCHITECTURAL_ANALYSIS_PIPELINE.md` et `docs/PHOTO_REASONING_LOOP.md` : analyse photo/multivue ;
- `docs/product/model-size-and-fidelity.md` : formats et niveaux de fidélité ;
- `docs/ARCHITECTURAL_LEGO_SOLUTIONS.md` : traduction LEGO ;
- `docs/NOTICE_DESIGN.md` : notice ;
- `docs/VIEWER.md` : inspection visuelle.

Les anciens documents de passation ou d'état peuvent dater. En cas de conflit, les principes, ADR, contrats/tests exécutables et l'état réel du dépôt restent prioritaires.

## 13. Critère de réussite final

Le parcours n'est réussi que lorsque l'utilisateur peut regarder la maquette et reconnaître son bâtiment, comprendre les simplifications assumées, vérifier qu'aucune certitude n'a été inventée pour faciliter le moteur, et disposer d'un modèle LEGO réellement constructible avec une notice cohérente.

La cible peut se résumer ainsi :

**vérité des pixels + compréhension architecturale multivue + fidélité perceptive + honnêteté des inconnues + constructibilité LEGO + notice claire.**
