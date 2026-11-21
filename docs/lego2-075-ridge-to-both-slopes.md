# LEGO2-075 — Liaison du faîtage à ses deux versants (une incompatibilité prouvée)

## Vérification concrète

Les études précédentes identifient les **tenons supérieurs LDraw 30363** de
chaque versant (060S/065), un couvre-faîtage transversal **26603 (2×3)**
et une brique de tête sur potelet **3002 (2×3)** (070–074).

Lorsque la **3002** est placée sous toute l'empreinte du couvre-faîtage,
ses **six tenons** se retrouvent au même niveau que les tenons supérieurs des
deux dernières pentes 30363. Dans la configuration nominale à deux versants
de 18° contrôlée, les deux tenons du côté négatif et les deux tenons du côté
positif réclament **quatre des mêmes cellules XY/Z** que les tenons de la 3002.

Or deux tenons **de pièces différentes** ne peuvent occuper exactement le
même cylindre physique à la même hauteur. Cela ne constitue pas une
« connexion » : c'est une **occupation simultanée impossible** pour cette
configuration. Le fait que la tuile 26603 possède dessous une cavité
compatible géométriquement avec une seule brique 3002 ne règle pas la
collision avec les **tenons des deux versants**.

**Verdict ciblé : `INVALID_DUPLICATED_STUD_OCCUPANCY`** pour la liaison
simultanée 3002 pleine largeur + deux pentes 30363 inchangées + tuile 26603.
Ce verdict ne dit **pas** qu'une brique 3002 et une 26603 ne peuvent
jamais s'emboîter seules.

## Amélioration logicielle

`assess_two_slope_ridge_connection(model, library=None, max_sites=8)`
dans `ridge_two_slope_joint_075.py` :
- réutilise le planificateur de couvre-faîtages 065, les vrais tenons
  30363 et le planificateur de potelets/appuis 070–074 ;
- vérifie les cellules (x, y, z) des **deux versants et de la 3002**,
  sans déplacer ni créer de pièce dans le modèle ;
- distingue le blocage **INVALID** d'une absence de preuve **UNKNOWN** ;
- réutilise les contrôles géométriques LDraw `_pair()` de 066
  sur les 5 paires locales (3002–versant négatif/positif,
  tuile–versant négatif/positif, versant–versant) lorsque la
  bibliothèque est disponible ; si elle ne l'est pas, les maillages
  restent inconnus mais la contradiction de tenons documentés subsiste.

## Une alternative LEGO réelle à étudier, mais PAS autorisée

**Ne pas utiliser une 3002 pleine largeur** à cet endroit. Le potelet
**1×1 central** de 070 pourrait éviter la duplication de tenons, parce
qu'il viserait une cellule intérieure distincte des deux lignes de tenons
des 30363. Il faudrait alors vérifier la capacité **réelle** de la
sous-face 26603 à s'engager **simultanément sur trois pièces** (1×1 central
et deux versants), la géométrie volumique, la hauteur, le chemin
d'insertion et la tenue structurelle.

Ce n'est **pas** une solution approuvée, car le vrai montage n'a pas été
démontré. La seconde orientation étudiée utilise une tuile 2×4 :
l'association à une tête 3002 demeure explicitement **UNKNOWN**.

Les vérifications LDraw de maillage fournissent un diagnostic supplémentaire
et non un certificat mécanique. Les autres assemblages alternatifs restent
à étudier sans inventer de liaison.

**Aucune pièce de GUIDED-004 n'est modifiée : 1 890 pièces conservées.**
Aucun versant déplacé, pente inchangée, appuis d'origine conservés.
**Statut général : NOT_CERTIFIED.**
