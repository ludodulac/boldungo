# BOLDÜNGO — ESCALIER L, DÉFINITION TOPOLOGIQUE V1 (photos 109)
**Cible : concept architectural de référence avant toute pièce LEGO**

## Lecture du trajet
- **DESCENTE depuis l'accès haut :** accès maison/plateforme en béton → volée haute parallèle au mur latéral Sud en direction Ouest → palier de rotation proche du coin arrière, dépassant la façade Ouest selon la vérité propriétaire → quart de tour **à gauche** en descente → volée basse vers Sud et cour → sol extérieur.
- **MONTÉE inverse :** sol dans la cour → volée basse vers le Nord → palier tournant → volée haute vers l'Est le long du mur de la maison → plateforme maçonnée de l'accès haut.
- Le vrai « L » et les parapets plein-hauteur sont des contraintes non négociables. La jonction haute se fait à la **maçonnerie**, et non directement au platelage bois. Le passage sous la plateforme doit rester vide.

## Preuves photographiques les plus instructives
- **Topologie de la volée haute et du palier** : `IMG_20261007_092854.jpg`, `IMG_20261007_092858.jpg` (en descente) ; `IMG_20261007_092813.jpg`, `IMG_20260930_155245.jpg` (en montée).
- **Partie basse / orientation extérieure du L** : `IMG_20261007_092901.jpg` (vue aérienne depuis palier), `IMG_20260919_170032.jpg`, `IMG_20260928_113255.jpg`, `IMG_20261007_094358.jpg`.
- **Haut : béton puis bois avec ressaut** : `IMG_20261007_092818.jpg`, `IMG_20260930_155302.jpg`.
- **Vide sous plateforme et dessous bois** : `IMG_20261007_092734.jpg`, `IMG_20260919_170019.jpg`.

### Paramètres fiables vs absents
```json
{
  "frame": "GUIDED004",
  "x_positive": "north",
  "y_positive": "west/back",
  "z_positive": "up",
  "house_x_interval_m": [0, 9.30],
  "house_y_interval_m": [0, 8.20],
  "stair_side": "south (x<0)",
  "stair_overruns_rear_plane": true,
  "rear_plane_y_m": 8.20,
  "descent_upper_run_axis": "+y west",
  "descent_lower_run_axis": "-x south",
  "descent_turn": "left, quarter turn",
  "total_flights": 2,
  "flight_step_count_values": [7,9],
  "which_flight_has_7": null,
  "which_flight_has_9": null,
  "clear_width_m": 1.12,
  "landing_shape": "approximately square",
  "landing_width_m": null,
  "landing_depth_m": null,
  "distance_behind_rear_wall_m": null,
  "flight_lengths_m": null,
  "riser_height_m": null,
  "tread_depth_m": null,
  "masonry_to_wood_transition": "one raised step/ledge visible, exact height unknown",
  "masonry_open_void": "REQUIRED",
  "mechanical_LEGO_validation": "NOT_STARTED"
}
```

Ces axes sont le **schéma topologique qualitatif**, issus de la déclaration propriétaire antérieure conservée dans `docs/evidence/module-003-masonry-terrace-stair-041.json` et corroborés par les photos. Ne pas interpréter les valeurs `null` comme 0.

### Pourquoi la scène 006/007 ne doit pas être recopiée
L'arrivée y≈4,50 m reste à l'intérieur de la profondeur y=8,20 m ; elle ne représente pas le trajet arrière décidé. Le point d'arrivée de l'escalier actuel et la position du béton/bois doivent être recalculés **ensemble** à partir du schéma en plan, sans changer la maison hôte.

### Étape unique suivante
Produire **un plan coté provisoire et orienté** de la maison comme contexte et du système E/P/T, en fixant un intervalle raisonnable pour le débord arrière à partir d'une échelle de référence, ou laisser la valeur non fixée si les preuves ne permettent pas de trancher. Faire valider la topologie visuellement avant une pièce LEGO. Puis définir uniquement les interfaces LEGO d'E↔P↔V, sans réouvrir 408 expériences de toit.
