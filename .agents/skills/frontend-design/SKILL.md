---
name: frontend-design
description: >-
  Directives et standards de design frontend pour concevoir et affiner des interfaces
  web modernes, humaines et professionnelles. À activer lors de la création ou
  l'amélioration de pages, composants, formulaires et feuilles de style pour éliminer
  le look "généré par IA", soigner la typographie, l'espacement et la réactivité mobile.
---

# Guide & Standards Frontend Design

Ce skill définit les principes directeurs pour construire et faire évoluer les interfaces utilisateur (UI/UX) avec un rendu sur mesure, distinctif, accessible et exempt des clichés visuels des templates générés par IA.

---

## 1. Éliminer le look "Généré par IA / Template Générique"

Les modèles d'IA ont tendance à reproduire certains motifs sur-utilisés. Voici les règles pour s'en affranchir :

| Cliché IA à proscrire | Approche recommandée |
|---|---|
| **Ombres lourdes et diffuses** (`box-shadow: 0 20px 50px ...` ou `z-depth-3/4/5`) | **Flat design & bordures subtiles** : `border: 1px solid rgba(0, 0, 0, 0.06)` avec ombre très légère (`box-shadow: 0 2px 10px rgba(0, 0, 0, 0.03)`). |
| **Icônes géantes dans des cercles colorés** (ex. cercle vert 80px sur pages de confirmation) | **Illustrations sobres ou badges intégrés** : taille mesurée, typographie soignée, hiérarchie visuelle naturelle. |
| **Boutons avec effet `pulse` permanent** | **Transitions douces au survol** : un léger `transform: translateY(-1px)` ou changement subtil d'accentuation. |
| **Dégradés violents ou formes d'arrière-plan abstraites** | **Fonds neutres et apaisants** : surfaces claires (`#f8fafc`, `#ffffff`) pour valoriser le contenu réel (photos, données). |
| **Pages trop denses sans respiration** | **Rythme spatial généreux** : espacement vertical (`padding: 4rem` à `5rem`) entre sections. |

---

## 2. Charte graphique & Cohérence de Marque

1. **Palette spécifique au projet** :
   * Toujours s'appuyer sur les variables CSS du thème (`:root`).
   * **Couleur primaire** : Bleu marine profond (`#1A2C5B`), assurant autorité et confiance.
   * **Accents identitaires** : Rouge (`#CE1126`), Jaune (`#FCD116`) ou Vert (`#009460`) utilisés avec parcimonie pour les actions clés (CTA, dons, alertes).
   * **Surfaces & Textes** : Blanc pur (`#ffffff`), fond gris très doux (`#f8fafc`), texte sombre à fort contraste (`#0f172a` / `#16202a`).
2. **Accessibilité des contrastes (WCAG AA)** :
   * Tout texte sur fond coloré doit avoir un ratio de contraste minimal de **4.5:1** (3:1 pour le grand texte).
   * Les textes d'aide ou libellés secondaires ne doivent jamais être trop clairs (éviter le gris en-dessous de `#64748b`).

---

## 3. Typographie & Hiérarchie

* **Titres expressifs** : Utiliser la police à empattement de la marque (ex. `Merriweather`) avec un interligne confortable (`1.2` à `1.3`).
* **Corps de texte lisible** : Police sans-serif moderne (ex. `Outfit`, `Inter`) avec interligne aéré (`line-height: 1.55` à `1.65`).
* **Poids de police modéré** : Réserver le gras (`font-weight: 700`) aux éléments clés (titres, CTA, chiffres d'impact) et privilégier `400` / `500` pour le reste.

---

## 4. Conception des Formulaires & Champs de Saisie

Les formulaires sont le cœur interactif de la plateforme (alertes, financements, dons). Ils exigent une attention particulière :

1. **Labels flottants sans collision** :
   * Pour les champs multilignes (`textarea`), le label actif doit monter suffisamment haut (`translateY(-22px)` à `-24px`) pour ne jamais couper la bordure supérieure ou être barré par le contour.
   * Assurer un `margin-top` suffisant sur le conteneur (`1.4rem` à `1.6rem`).
2. **Indicateurs de focus nets et adaptés** :
   * Pour les champs avec ligne inférieure (style Materialize), désactiver les contours rectangulaires génériques (`outline: none !important`) qui coupent le texte, et animer la bordure inférieure (`border-bottom: 1px solid var(--accent)`).
3. **Feedback de soumission accessible (Anti-double clic)** :
   * Désactiver le bouton dès le clic (`disabled`, `aria-disabled="true"`).
   * Afficher un spinner fluide (`.form-submit-spinner`) et passer le libellé en *« Envoi en cours… »*.
   * Toujours intégrer un conteneur vocal et visuel `<p role="status" aria-live="polite">` pour notifier les technologies d'assistance.
4. **Cibles tactiles mobiles** :
   * Boutons et champs d'une hauteur minimale de **44px à 48px** pour un confort tactile optimal sur smartphone.

---

## 5. Responsivité & Expérience Mobile

1. **Mobile-First dès la conception** :
   * Tester les largeurs réelles : 360px, 390px (iPhone), 768px (tablette) et 1200px+ (desktop).
2. **Éléments flottants non-obstructifs** :
   * Les bannières (cookies, annonces) doivent être compactes sur mobile (hauteur max 40vh, texte resserré, boutons compacts) pour ne jamais bloquer l'accès aux formulaires ou boutons principaux.
3. **Logos adaptatifs** :
   * Dans la barre de navigation mobile/desktop compacte : privilégier l'emblème ou logo carré (ex. 52×52px) pour une visibilité immédiate.
   * Le logo complet (avec typographie et slogan) est réservé au pied de page et aux zones de présentation.
4. **Respect des préférences utilisateur** :
   * Toujours intégrer `@media (prefers-reduced-motion: reduce)` pour désactiver les rotations et animations continues pour les personnes sensibles.

---

## 6. Liste de Contrôle (Checklist Avant Validation)

Avant de valider une interface ou un composant :
- [ ] Le design est-il épuré, calme et crédible sans surcharge d'ombres ?
- [ ] Les couleurs correspondent-elles à la charte officielle ?
- [ ] Les formulaires disposent-ils d'un état de chargement et d'anti-double clic ?
- [ ] Les labels flottent-ils clairement sans être barrés par un trait ou un outline ?
- [ ] Le rendu est-il fluide et dégagé sur mobile (390px) ?
- [ ] Aucun composant ne dépasse horizontalement de l'écran (`overflow-x`).
