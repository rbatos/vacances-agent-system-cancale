# Procédure d'utilisation des agents pour préparer le séjour

Ce guide décrit un cycle de préparation efficace avec les agents Copilot du projet Cancale, depuis la vérification du contexte jusqu'aux livrables. Il complète la [procédure de transformation du projet](PROCEDURE_TRANSFORMATION_PROJET.md), qui traite de l'évolution du dépôt d'origine.

## Règle de décision

Les agents recherchent, vérifient et recommandent; la famille décide. Une idée proposée n'est pas une étape validée, une étape validée n'est pas nécessairement planifiée, et une étape planifiée n'est pas une réservation. L'orchestrateur ne modifie `vacances_data.json` qu'après une autorisation explicite portant sur les éléments à inscrire. La famille n'a pas à éditer le JSON.

## Point à régler avant la première planification

Dans l'état du dépôt consulté pour rédiger ce guide, la charte et certaines consignes indiquent que les listes de sorties sont vides, alors que `vacances_data.json` contient neuf étapes. Ne présume pas que toutes ces étapes ont été validées. Demande à `vacances-conseil` de comparer la charte, les consignes et le JSON sans rien modifier; la famille devra clarifier le statut des éléments contradictoires avant toute nouvelle écriture ou génération de livrables.

**Prompt de vérification initiale :**

> Lis la charte active, les consignes Copilot et `vacances_data.json`. Résume les faits confirmés et compare le statut des sorties, du budget, des Plans B et des checklists entre ces sources. Signale toute contradiction et arrête-toi sans modifier de fichier ni lancer les générateurs.

## Cycle recommandé

### 1. Ouvrir la bonne session

Dans VS Code, utilise le harness Copilot et sélectionne l'agent **vacances-conseil**. Garde les demandes d'un même sujet dans le même fil pour que l'orchestrateur conserve le contexte. Les agents spécialisés sont normalement invoqués par lui; il n'est pas nécessaire de les appeler tous à chaque question.

Commence par le prompt de vérification initiale ci-dessus si le statut des données n'est pas clair. Si un spécialiste n'est pas appelé ou si son appel échoue, demande à l'orchestrateur de le signaler : une analyse directe ne doit pas être présentée comme un avis délégué.

### 2. Définir une demande exploitable

Indique la décision à prendre, les contraintes concernées, les préférences réellement exprimées et le niveau de détail attendu. Ne fournis pas de données personnelles ou de réservation dans les fichiers partagés.

Exemples de demandes : trouver quelques idées de sorties, comparer deux activités, vérifier un trajet, arbitrer une dépense, envisager un Plan B ou préparer une checklist. Évite de demander simultanément un programme complet, les réservations, le budget réel et les bagages si ces décisions ne sont pas mûres.

### 3. Chercher des idées, puis faire vérifier les candidates

Pour des sorties ou une comparaison d'activités, invoque `/vacances-nouvelle-etape` ou demande directement à `vacances-conseil`. L'orchestrateur choisit les spécialistes pertinents :

- **Scout famille** : enfant de moins de 3 ans et enfant de 7 ans, marche, durée, poussette ou porte-bébé, sanitaires, sécurité, pauses et possibilité d'écourter;
- **Navigateur logistique** : conduite depuis Cancale, temps aller, retour et cumul, stationnement, pauses et faisabilité;
- **Trésorier** : coût total pour quatre, gratuités, tarifs confirmés ou estimations et impact sur l'enveloppe locale;
- **Sentinelle météo** : pluie, vent, marées, horaires de marée, activités couvertes et repos au logement.

Ne demande pas à chaque rôle de répéter les mêmes recherches. Une sortie côtière mobilise naturellement la Sentinelle; une question de budget seule mobilise surtout le Trésorier. Pour des idées nouvelles, le Scout et le Navigateur sont les vérifications de base.

**Prompt de recherche :**

> Propose six à huit sorties candidates depuis Cancale, sans les inscrire dans les données. Pour chacune, demande au Scout famille et au Navigateur de vérifier les points relevant de leur rôle; ajoute le Trésorier et la Sentinelle quand c'est pertinent. Vise au plus 3 h de conduite aller-retour; distingue clairement les estimations à la limite ou au-delà, et prends en compte l'âge des enfants (moins de 3 ans et 7 ans). Distingue faits issus de sources, estimations et inconnues, puis recommande une courte sélection sans la déclarer validée.

### 4. Comparer avec des éléments vérifiables

Demande une restitution comparable, idéalement sous forme de tableau. Pour chaque candidate, vérifie ou fais préciser :

- intérêt et contraintes concrètes pour les deux enfants;
- durée sur place, marche, accès poussette/porte-bébé, sanitaires, sécurité et possibilité d'écourter;
- durée de conduite aller, retour et total, avec source ou statut d'estimation;
- prix pour les quatre personnes, repas, stationnement et autres coûts pertinents;
- ouverture et horaires applicables aux dates du séjour;
- météo, vent et marée lorsque l'activité y est sensible;
- solution de repli et informations restant à confirmer.

Privilégie les sources officielles actuelles pour horaires et tarifs. Une durée de trajet calculée sans trafic reste une estimation. Une prévision météo à long terme n'est pas un fait confirmé; les horaires de marée et les prévisions doivent correspondre aux dates concernées.

**Prompt de comparaison :**

> Compare ces candidates dans un tableau. Sépare les faits vérifiés, les estimations et les inconnues; indique les sources et la date de vérification. Donne le coût famille et les durées aller/retour/cumul. Signale toute candidate qui dépasse 180 minutes de conduite cumulée; si je demande de la conserver à titre de comparaison, ne la présente pas comme conforme.

### 5. Choisir le rythme avant de fixer les jours

Commence par retenir les activités que la famille souhaite réellement faire. Ensuite seulement, demande une proposition de rythme : sorties courtes et longues alternées, temps de repos, contraintes d'ouverture, météo et marées. Garde de la souplesse et une possibilité d'écourter; ne transforme pas une idée en rendez-vous ou réservation.

Pour un aléa précis, invoque `/vacances-plan-b` avec la sortie, la date envisagée et le risque (pluie, vent, marée ou fatigue). La Sentinelle examine le repli, puis le Navigateur et le Trésorier sont consultés selon le trajet et le coût. Le repos à Cancale reste une option valable.

### 6. Suivre le budget sans inventer de dépenses

Invoque `/vacances-budget` pour une estimation ou un arbitrage. L'enveloppe de 300 à 500 EUR porte sur les dépenses sur place, hors hébergement et trajet jusqu'à Cancale, sauf précision contraire. Demande les coûts famille, les activités gratuites, les estimations et la marge restante.

Le skill actuel produit une estimation, pas un registre de transactions : ne demande pas d'inscrire des dépenses réelles dans `budget.postes` ni de les présenter comme payées. Toute évolution du modèle de budget nécessite une décision distincte.

### 7. Valider explicitement avant toute mise à jour

Quand la famille a choisi, formule une autorisation sans ambiguïté, par exemple :

> J'autorise l'inscription dans `vacances_data.json` des sorties A et B comme étapes retenues, sans leur attribuer de jour ni les présenter comme réservées. Ne change rien d'autre.

L'orchestrateur doit alors modifier uniquement ces éléments, préserver le schéma et montrer ce qui a changé. Une validation de sortie n'autorise pas à ajouter un jour, une réservation, un tarif ou une activité connexe. Si le statut d'une donnée est ambigu, il doit demander confirmation avant l'écriture.

### 8. Générer et contrôler les livrables

Après la mise à jour validée, demande à l'orchestrateur de vérifier le JSON puis de lancer `py sync_system.py` si tu souhaites régénérer la carte, le carnet et le dashboard. Le script produit des vues à partir des données; il ne remplace pas leur validation et ne met pas à jour le JSON.

Contrôle que les sorties affichées correspondent aux choix, que les données inconnues restent signalées, et que les horaires, jours ou réservations non confirmés ne sont pas présentés comme acquis. La carte utilise des services externes et nécessite une connexion; les fonds de tuiles peuvent avoir leurs propres restrictions.

### 9. Préparer le départ au bon moment

Quand les activités et les informations utiles sont suffisamment stables, invoque `/vacances-checklist-depart`. Le Scout, le Navigateur et la Sentinelle sont consultés selon le contenu. Demande de distinguer les choses à vérifier de ce que la famille possède ou a réservé : aucun matériel, billet ou équipement ne doit être supposé disponible.

À l'approche du séjour, refais les vérifications sensibles au temps : ouverture, réservation, météo, vigilance, marées et trajets. Ne traite pas une recherche faite plusieurs semaines plus tôt comme une confirmation actuelle.

## Contrôle de la délégation dans VS Code

La présence des agents dans le sélecteur confirme leur découverte, pas leur invocation. Pour tester le fonctionnement :

1. sélectionner le harness Copilot et `vacances-conseil`;
2. envoyer une demande qui nécessite deux avis distincts, par exemple l'adaptation aux enfants et le trajet;
3. vérifier dans l'activité de la conversation que les sous-agents attendus ont réellement été appelés;
4. vérifier que la synthèse nomme les avis reçus et les appels manquants.

Ne conclus pas à une délégation réussie si l'orchestrateur se contente de décrire les rôles.

## Commandes disponibles

- `/vacances-nouvelle-etape` : proposer ou comparer des sorties;
- `/vacances-plan-b` : rechercher un repli face à un aléa;
- `/vacances-budget` : estimer et arbitrer les dépenses sur place;
- `/vacances-checklist-depart` : préparer les vérifications et affaires de départ.

Pour une demande qui traverse plusieurs sujets, sélectionner `vacances-conseil` et le laisser déléguer les vérifications pertinentes.
