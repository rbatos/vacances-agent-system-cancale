---
name: Charte du séjour familial
description: Utiliser pour toute recommandation, évaluation ou modification de l'itinéraire, du budget, des hébergements, des Plans B ou des checklists du séjour.
---

# Charte Copilot du séjour à Cancale

Cette charte autonome définit les règles métier du séjour actuellement préparé avec GitHub Copilot. Elle est la référence pour les agents et skills de ce projet.

- **Hébergement fixe :** Cancale; construire des idées de sorties en étoile, sans changer le logement.
- **Dates :** du 25 octobre 2026 au 1er novembre 2026 inclus.
- **Famille :** deux adultes dans la quarantaine, un enfant de 7 ans et un enfant de 3 ans. Aucun intérêt particulier ni genre d'enfant n'est défini; ne pas en inventer.
- **Budget :** enveloppe cible de 300 à 500 EUR pour les dépenses sur place de la famille. Le coût du logement et du trajet jusqu'à Cancale est exclu, sauf précision contraire de la famille.
- **Déplacements :** maximum de 2 h de conduite cumulée aller-retour depuis Cancale pour une sortie. Afficher séparément l'aller, le retour et le total; signaler toute proposition qui dépasse cette limite.

`vacances_data.json` a été migré pour contenir uniquement les éléments confirmés du séjour Cancale et conserve son schéma. Il décrit le profil, les dates, l'hébergement fixe et l'enveloppe; ses listes d'activités, de postes budgétaires, de checklists et de Plans B sont vides, donc aucune sortie ni réservation n'est encore validée. Ne réutilise aucune ancienne activité, réservation ou montant du road trip.

- La famille valide les décisions. Présente des propositions; ne prétends pas qu'une activité est choisie ou réservée sans confirmation.
- Adapte chaque proposition aux deux enfants : durée réaliste, marche et dénivelé, accès poussette/porte-bébé, sanitaires, repas, repos, sécurité et possibilité d'écourter. N'invente pas leurs intérêts.
- Respecte le rayon de 2 h de conduite cumulée aller-retour depuis Cancale. Ne confonds pas durée aller et durée totale.
- Pour le budget, calcule le coût total pour quatre personnes et distingue tarifs vérifiés, estimations et gratuités. Reste dans l'enveloppe sur place de 300 à 500 EUR; le logement et le trajet jusqu'à Cancale sont exclus sauf indication contraire.
- Pour toute sortie côtière ou extérieure en automne, vérifie météo, vent, marées et horaires de marée applicables. Propose une alternative couverte ou le repos au logement si nécessaire.
- Ne fabrique aucun horaire, prix, durée de trajet, disponibilité, réservation, état de marée ou météo. Privilégie les sources officielles actuelles; marque les inconnues et les estimations.
- Les sous-agents spécialistes consultent, vérifient et proposent; ils ne modifient aucun fichier. L'orchestrateur présente leurs avis et attend la validation familiale avant toute décision persistante.
- Les sous-agents consultent les données et proposent; seul l'orchestrateur reporte dans `vacances_data.json` les sorties, coûts ou checklists explicitement validés par la famille. Préserve le schéma et ne demande jamais à la famille d'éditer le JSON à la main.
- N'inscris aucune référence de réservation, adresse privée ni donnée nominative. Les dates du séjour ci-dessus sont explicitement autorisées comme contexte du projet.
- Les profils spécialisés sont définis directement dans `.github/agents/`; leurs critères doivent rester cohérents avec cette charte.