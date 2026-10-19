# Procédure de transformation d'un projet vacances

Cette procédure reprend le chemin suivi pour faire évoluer `vacances-agent-system` vers un projet de séjour fixe à Cancale, piloté par GitHub Copilot. Elle peut servir de modèle pour adapter le projet à une autre famille ou destination.

Elle concerne la transformation du dépôt. La procédure d'utilisation quotidienne des agents pour préparer un voyage est un sujet distinct.

## Principes à préserver

- Garder le projet original intact et travailler dans une copie ou un nouveau dépôt.
- Faire valider le contexte du séjour et les décisions persistantes par la famille.
- Préserver le schéma des données existantes tant qu'une évolution n'est pas explicitement décidée.
- Faire proposer et vérifier les éléments par les agents; seul l'orchestrateur inscrit dans les données les décisions explicitement validées.
- Ne supprimer aucun fichier avant d'avoir vérifié ses dépendances et obtenu l'accord demandé.
- Distinguer les sources de vérité, les fichiers générés et les archives.
- Vérifier les mécanismes Copilot dans la version réellement utilisée; ne pas présumer qu'un format de personnalisation Antigravity est directement compatible.

## Étapes

### 1. Créer une copie de travail

1. Conserver le dépôt original sans modification.
2. Copier ou cloner le projet dans un nouvel emplacement correspondant au nouveau séjour.
3. Vérifier le dépôt actif, son dossier racine, son état Git et les éventuelles modifications préexistantes.
4. Définir les limites de périmètre : fichiers autorisés, fichiers à préserver et opérations qui nécessitent une validation préalable.

**Résultat attendu :** une copie indépendante, dont les changements ne risquent pas d'altérer le projet transmis.

### 2. Inventorier avant de modifier

Lire le README, les données, les instructions, les agents, les skills, les workflows, les scripts et les fichiers générés. Pour chaque élément, noter son rôle, ses entrées, ses sorties et ses références croisées.

Classer ensuite les éléments en quatre groupes :

- conserver tels quels;
- adapter au nouveau séjour;
- archiver, si l'historique reste utile;
- supprimer éventuellement, après accord.

Ne pas conclure qu'un script est inutile parce qu'il contient des données héritées. Un générateur de carte, de carnet ou de tableau de bord peut souvent être adapté; un orchestrateur simulant des avis codés en dur n'est pas pour autant le moteur des sous-agents Copilot.

**Prompt utile :**

> Inventorie ce dépôt sans modifier ni supprimer de fichier. Pour chaque fichier important, indique son rôle, ses dépendances et s'il faut le conserver, l'adapter, l'archiver ou envisager sa suppression. Termine par les questions qui exigent une décision de ma part.

### 3. Définir le séjour cible

Avant l'adaptation, réunir les informations confirmées :

- point d'hébergement fixe et dates;
- composition du groupe et besoins connus;
- budget, avec inclusion et exclusion clairement explicitées;
- limite de déplacement et définition de cette limite (par exemple, conduite aller-retour);
- contraintes saisonnières, d'accessibilité ou de rythme;
- règles de confidentialité et limites d'autonomie des agents.

Écrire ces règles dans une charte autonome, utilisée comme référence prioritaire. Signaler les inconnues plutôt que de les compléter par supposition.

**Prompt utile :**

> À partir des informations confirmées suivantes, rédige la charte métier du nouveau séjour. Sépare les faits confirmés des inconnues, n'invente aucune activité ni réservation, et précise les règles de validation familiale et de confidentialité. Ne modifie pas encore les données ni les autres fichiers.

### 4. Adapter les personnalisations à Copilot

Vérifier la documentation et les capacités du Copilot réellement utilisé dans VS Code avant de choisir les formats. Dans le projet Cancale, l'organisation active repose sur :

- `.github/copilot-instructions.md` pour les consignes générales du dépôt;
- `.github/instructions/` pour la charte et les règles ciblées;
- `.github/agents/*.agent.md` pour l'orchestrateur et les spécialistes;
- `.github/skills/<nom>/SKILL.md` pour les procédures invocables.

Traduire les responsabilités métier, pas seulement renommer les fichiers :

1. Créer un agent orchestrateur chargé de cadrer la demande, choisir les spécialistes pertinents, consolider leurs retours et présenter une décision à la famille.
2. Créer un profil par rôle spécialisé, avec son périmètre, ses critères de vérification, ses sources attendues et ses limites d'écriture.
3. Déclarer explicitement les sous-agents autorisés à l'orchestrateur si le format Copilot utilisé le permet.
4. Relier les skills aux agents appropriés et à la charte active.
5. Retirer les consignes héritées contradictoires après avoir vérifié qu'elles ne sont plus nécessaires.

Les spécialistes doivent analyser et proposer, pas modifier les données du séjour. L'orchestrateur ne persiste une décision qu'après accord explicite de la famille.

**Prompt utile :**

> Adapte les rôles et workflows existants aux mécanismes Copilot actuellement documentés pour mon environnement. Commence par vérifier les formats pris en charge. Propose les fichiers et les références à créer ou modifier, conserve les règles métier utiles, et ne supprime encore aucune source héritée.

### 5. Migrer les données de façon contrôlée

1. Repérer le schéma et les usages de chaque champ dans le code.
2. Remplacer les seules données héritées nécessaires au profil du nouveau séjour, après autorisation explicite.
3. Conserver la structure JSON existante, sauf décision distincte sur son évolution.
4. Laisser les listes d'activités, de dépenses, de checklists ou de Plans B vides tant qu'aucun élément correspondant n'a été validé.
5. Ne pas confondre `vacances_data.json`, source structurée du séjour, avec les livrables HTML générés.
6. Vérifier le JSON et les hypothèses métier avant de régénérer les livrables.

**Prompt utile :**

> J'autorise la migration des seules données de profil confirmées vers le nouveau séjour. Préserve le schéma existant, n'invente aucun choix, tarif ou réservation, et laisse les listes non validées vides. Présente les changements et valide le JSON avant toute génération.

### 6. Adapter les outils et livrables

Pour chaque générateur, identifier ses entrées, ses sorties et les éventuelles données codées en dur. Adapter les outils utiles pour qu'ils lisent la source actuelle, au lieu de recopier les anciens contenus :

- carte : point de base, marqueurs des destinations réellement présentes et sources cartographiques;
- carnet imprimable : profil, dates, sorties et informations manquantes;
- tableau de bord : données du séjour courant, états vides explicites et absence de contenu hérité;
- script de synchronisation : orchestration des générateurs sans écriture implicite dans le JSON.

Pour les géocodages et fonds de carte, respecter les conditions des services utilisés, conserver l'attribution requise, limiter et mettre en cache les requêtes, et signaler les repères approximatifs. Ne pas présenter un point d'accès comme l'adresse exacte d'un lieu.

Tester chaque générateur séparément avant le script global. Lancer le script global seulement après validation des données qu'il va publier.

### 7. Nettoyer les héritages avec accord

Avant toute suppression :

1. Rechercher les références au fichier dans le dépôt.
2. Vérifier les imports, appels de scripts, liens du README et références dans les agents, skills et instructions.
3. Proposer des groupes de suppression avec leurs conséquences.
4. Attendre l'accord explicite pour les suppressions.
5. Supprimer les références devenues obsolètes dans la même opération.
6. Rechercher à nouveau les noms et chemins retirés.

Traiter les scripts séparément des livrables historiques : les premiers peuvent être adaptables, les seconds peuvent être des archives utiles. Ne pas supprimer les données ou archives au seul motif qu'elles ne sont pas utilisées par le nouveau flux.

**Prompt utile :**

> Fais un audit des fichiers hérités sans rien supprimer. Pour chaque candidat, donne les références restantes, les conséquences d'une suppression et une proposition de groupe cohérent. Attends ma validation explicite avant toute suppression.

### 8. Valider le résultat

Contrôler au minimum :

- les données sont lisibles et conformes au schéma attendu;
- les termes et destinations de l'ancien séjour ne fuient pas dans les nouveaux livrables;
- les générateurs s'exécutent et produisent les fichiers attendus;
- les sorties non planifiées ou non validées sont présentées comme telles;
- les chemins et commandes du README sont exacts;
- les instructions, agents et skills ne se contredisent pas;
- Copilot découvre les agents et skills dans VS Code;
- une demande de test à l'orchestrateur montre de vrais appels aux spécialistes, pas seulement leur description;
- les spécialistes n'écrivent pas dans les fichiers et l'orchestrateur demande l'accord avant toute persistance.

La découverte d'un agent ne prouve pas que la délégation fonctionne. Faire un test dans le harness Copilot réellement utilisé et vérifier l'activité visible de la conversation. Rapporter les limites non vérifiées au lieu de conclure que tout fonctionne.

### 9. Mettre à jour la documentation

Documenter le nouveau profil, les agents et skills disponibles, les commandes de génération, les dépendances réseau, les sorties produites et les validations réellement exécutées. Conserver la chronologie historique séparée du guide opérationnel pour qu'elle ne soit pas interprétée comme une consigne active.

## Critères de fin

La transformation est prête lorsque le dépôt de travail est autonome, que le contexte et les règles du séjour sont cohérents, que les données ne contiennent que les décisions validées, que les générateurs utilisent ces données, que les références héritées sont maîtrisées et que la délégation Copilot a été testée dans l'environnement cible.
