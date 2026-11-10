# BOLDÜNGO — M029 — PREMIER LOGEMENT SOUS LA PENTE

**Statut avant exécution : analyse locale préparée, verdict non encore mesuré.**

Le script cible **uniquement** le tenon réel de `gable-000006` (3004) au centre mondial **(470, −792, 50)** LDU, correspondant au site local **(10, 24, 0)** sous `roof-000048` (30363) dans le modèle B3 inchangé.

Il vérifie avec les véritables fichiers épinglés `pybricks/ldraw` :
- rayon et hauteur de `p/stud.dat` ;
- tube `p/stud4a.dat` documenté dans `parts/s/30363s01.dat:18` ;
- faces intérieures `parts/s/30363s01.dat:48,54` ;
- distances de surface tenon/tube/parois et trajets d'insertion **virtuels** sur le seul tenon isolé.

La compatibilité nominale A ne peut être affirmée qu'après exécution sans signal de traversée de maillage sur les échantillons. Cela ne prouvera pas la stabilité, les tolérances ou l'insertion de la brique entière. Si les données ne suffisent pas, le verdict reste **C — INDÉTERMINÉ**.

Aucune pièce B3, aucune règle physique et aucun moteur modifiés.
