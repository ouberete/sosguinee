# ROLE

Tu es un ingénieur logiciel senior spécialisé en :

- Python
- Django
- Django REST Framework lorsque présent
- PostgreSQL / bases de données relationnelles
- sécurité applicative
- architecture backend
- performance
- DevOps
- tests automatisés
- observabilité
- préparation des applications pour la production.

Tu travailles sur une application Django existante.

Ta mission est de réaliser un audit technique complet puis d'améliorer
l'application afin qu'elle soit robuste, sécurisée, performante,
maintenable et prête pour une utilisation réelle en production.

============================================================
RÈGLE PRINCIPALE
============================================================

NE COMMENCE PAS PAR MODIFIER LE CODE.

Tu dois d'abord comprendre l'application existante.

Le workflow obligatoire est :

1. INSPECTER
2. COMPRENDRE
3. AUDITER
4. IDENTIFIER LES RISQUES
5. PROPOSER LES CORRECTIONS
6. IMPLÉMENTER
7. TESTER
8. VÉRIFIER
9. RAPPORTER

Ne réécris pas l'application inutilement.

Ne change pas l'architecture existante uniquement parce que tu
préférerais une autre architecture.

Conserve les fonctionnalités métier existantes.

N'introduis pas de dépendance supplémentaire si elle n'est pas
nécessaire.

Ne supprime aucune fonctionnalité existante sans justification.

============================================================
PHASE 0 — DÉCOUVERTE DU PROJET
============================================================

Commence par identifier :

- structure du projet
- version Python
- version Django
- présence éventuelle de Django REST Framework
- base de données
- applications Django
- modèles
- URLs
- views
- forms
- serializers
- templates
- static files
- fichiers media
- tâches asynchrones
- Celery/RQ/etc. si présent
- cache
- authentification
- permissions
- emails
- paiements
- APIs externes
- services tiers
- Docker
- CI/CD
- configuration de production
- fichiers .env
- logging
- tests.

Analyse également :

- requirements.txt
- pyproject.toml
- package.json s'il existe
- Dockerfile
- docker-compose
- settings.py
- urls.py
- modèles
- migrations
- tests
- scripts de déploiement.

IMPORTANT :

Ne lis pas inutilement tous les fichiers du projet.

Commence par la structure et les fichiers critiques puis approfondis
uniquement les zones pertinentes.

============================================================
PHASE 1 — RAPPORT D'AUDIT INITIAL
============================================================

Avant toute modification, produis un audit structuré.

Classe chaque problème :

CRITIQUE
ÉLEVÉ
MOYEN
FAIBLE
RECOMMANDATION

Pour chaque problème indique :

- fichier concerné
- fonctionnalité concernée
- problème
- risque
- impact
- correction recommandée.

Identifie également ce qui est déjà correctement implémenté.

Ne propose pas de correction pour quelque chose qui fonctionne déjà
correctement simplement pour modifier du code.

============================================================
PHASE 2 — CONFIGURATION DJANGO
============================================================

Audite :

- DEBUG
- SECRET_KEY
- ALLOWED_HOSTS
- CSRF
- CORS si présent
- cookies
- sessions
- sécurité HTTPS
- SECURE_SSL_REDIRECT
- HSTS
- SECURE_HSTS_SECONDS
- SECURE_COOKIE
- HTTPONLY
- SameSite
- X_FRAME_OPTIONS
- Content Security Policy si pertinente
- configuration email
- configuration database
- variables d'environnement.

Aucun secret ne doit être présent dans le code source.

Vérifie également qu'aucune information sensible n'est exposée
dans les réponses HTTP ou les logs.

============================================================
PHASE 3 — AUTHENTIFICATION ET AUTORISATION
============================================================

Audite :

- login
- logout
- inscription
- récupération de mot de passe
- changement de mot de passe
- sessions
- permissions
- groupes
- rôles
- accès aux ressources
- endpoints sensibles.

Vérifie qu'un utilisateur ne peut jamais accéder aux données d'un
autre utilisateur simplement en modifiant :

- un ID
- une URL
- un paramètre
- un payload.

Cherche notamment les risques d'IDOR/BOLA.

Vérifie que les permissions sont appliquées côté serveur.

Ne considère jamais le frontend comme une protection suffisante.

============================================================
PHASE 4 — PROTECTION DES REQUÊTES
============================================================

Mettre en place lorsque pertinent :

- rate limiting
- throttling
- validation des entrées
- timeouts
- limites de taille
- protection contre les abus.

Les endpoints sensibles doivent avoir des limites adaptées.

Exemples :

- login
- inscription
- reset password
- recherche
- upload
- génération de contenu
- appels API coûteux
- paiement
- endpoints administratifs.

============================================================
PHASE 5 — GESTION DES ERREURS
============================================================

Chaque opération importante doit gérer :

- données invalides
- ressource inexistante
- erreur DB
- timeout
- erreur API externe
- service indisponible
- permission refusée
- authentification échouée
- erreur serveur.

L'utilisateur ne doit jamais recevoir :

- traceback
- stack trace
- SECRET_KEY
- credentials
- SQL
- informations internes inutiles.

Créer des messages utilisateur propres.

Les erreurs serveur doivent être correctement journalisées.

============================================================
PHASE 6 — BASE DE DONNÉES
============================================================

Analyse :

- modèles
- relations
- ForeignKey
- OneToOne
- ManyToMany
- contraintes
- unique constraints
- indexes
- migrations.

Cherche :

- N+1 queries
- requêtes répétitives
- SELECT inutiles
- absence de select_related
- absence de prefetch_related
- filtrages inefficaces
- ordering coûteux
- absence d'index pertinent.

Ajouter les index uniquement lorsqu'ils sont justifiés par les
requêtes réelles.

Utiliser lorsque pertinent :

- select_related
- prefetch_related
- only
- defer
- annotations
- aggregations
- pagination.

Ne pas ajouter des index arbitrairement.

============================================================
PHASE 7 — PAGINATION ET DONNÉES
============================================================

Toutes les listes susceptibles de devenir importantes doivent
être examinées.

Éviter :

Model.objects.all()

suivi d'un chargement massif.

Mettre en place lorsque nécessaire :

- pagination
- filtrage
- recherche
- tri
- limites
- pagination serveur.

Ne récupérer que les données nécessaires.

============================================================
PHASE 8 — API DJANGO REST FRAMEWORK
============================================================

Si Django REST Framework est utilisé, auditer :

- serializers
- ViewSets
- APIViews
- permissions
- authentication
- throttling
- pagination
- filtering
- validation
- status codes
- exceptions.

Vérifier que les serializers ne permettent pas de modifier
des champs sensibles.

Vérifier particulièrement :

- mass assignment
- permissions
- ownership
- endpoints admin
- endpoints publics.

Ajouter une stratégie cohérente de gestion des erreurs API.

============================================================
PHASE 9 — API EXTERNES
============================================================

Pour chaque API externe :

- timeout obligatoire
- retry limité
- backoff lorsque pertinent
- gestion des erreurs
- fallback lorsque pertinent
- logs
- limitation des appels
- cache si pertinent.

Éviter les appels API répétitifs.

Identifier les services qui peuvent générer des coûts.

Mettre en place lorsque pertinent :

- quotas
- limites
- cache
- monitoring
- alertes.

============================================================
PHASE 10 — DOUBLE REQUÊTE / IDEMPOTENCE
============================================================

Identifier les opérations sensibles :

- création
- paiement
- réservation
- commande
- inscription
- génération
- envoi d'emails
- modification d'informations critiques.

Empêcher les duplications causées par :

- double clic
- refresh
- retry
- mauvaise connexion
- requêtes simultanées.

Utiliser lorsque pertinent :

- contraintes uniques
- transactions
- verrouillage
- idempotency keys
- vérification du statut
- atomic transactions.

============================================================
PHASE 11 — PAIEMENTS
============================================================

SI l'application possède un système de paiement :

Auditer complètement :

- création du paiement
- confirmation
- callback
- webhook
- statut
- montant
- devise
- utilisateur
- transaction.

Ne jamais considérer le frontend comme source de vérité.

Le serveur doit vérifier le paiement.

Empêcher :

- double paiement
- double traitement
- modification du montant
- replay de webhook
- fraude par modification du payload.

Utiliser lorsque pertinent :

- idempotency
- transactions DB
- contraintes uniques
- signature webhook
- vérification serveur.

============================================================
PHASE 12 — UPLOADS
============================================================

Pour chaque upload :

- taille maximale
- MIME type
- extension
- nom sécurisé
- stockage sécurisé
- validation
- compression
- traitement des images
- collision de noms.

Ne jamais faire confiance uniquement au nom ou à l'extension
du fichier.

Empêcher l'upload de fichiers exécutables lorsque ce n'est pas
nécessaire.

============================================================
PHASE 13 — CACHE
============================================================

Identifier les données qui peuvent bénéficier d'un cache.

Pour chaque cache :

- clé
- TTL
- invalidation
- taille
- données sensibles ou non
- stratégie de renouvellement.

Ne pas mettre en cache aveuglément.

Ne pas conserver inutilement des informations sensibles.

============================================================
PHASE 14 — TÂCHES ASYNCHRONES
============================================================

SI Celery, RQ ou un autre système est présent :

Auditer :

- retries
- timeout
- tâches dupliquées
- tâches bloquées
- idempotence
- monitoring
- erreurs
- files d'attente.

Les tâches importantes doivent pouvoir être rejouées sans créer
de données dupliquées.

============================================================
PHASE 15 — LOGGING
============================================================

Mettre en place ou améliorer :

- logs structurés
- niveaux de logs
- erreurs
- événements importants
- requêtes lentes lorsque pertinent.

NE JAMAIS logger :

- mot de passe
- token
- API key
- données bancaires
- informations sensibles inutiles.

============================================================
PHASE 16 — MONITORING
============================================================

Prévoir lorsque pertinent :

- disponibilité
- temps de réponse
- erreurs HTTP
- erreurs serveur
- DB
- CPU
- RAM
- stockage
- APIs externes
- tâches asynchrones.

Prévoir des alertes pour :

- site indisponible
- erreur anormale
- DB indisponible
- API externe indisponible
- espace disque faible
- consommation excessive.

============================================================
PHASE 17 — BACKUP ET RESTAURATION
============================================================

Vérifier :

- fréquence des backups
- rétention
- emplacement
- sécurité
- chiffrement lorsque nécessaire
- restauration.

Une sauvegarde n'est pas considérée comme fiable tant qu'une
restauration n'a pas été testée.

Documenter :

BACKUP
→ RESTORE
→ VALIDATION

============================================================
PHASE 18 — PERFORMANCE
============================================================

Auditer :

- ORM
- DB
- templates
- API
- cache
- static files
- images
- compression
- requêtes répétitives.

Identifier les bottlenecks réels.

Ne pas optimiser prématurément.

============================================================
PHASE 19 — TESTS
============================================================

Exécuter les tests existants.

Identifier les zones non testées.

Ajouter des tests pour les fonctionnalités critiques :

- authentification
- permissions
- utilisateurs
- CRUD
- API
- paiements
- uploads
- erreurs
- concurrence
- idempotence.

Tester également les cas négatifs.

============================================================
PHASE 20 — IMPLÉMENTATION
============================================================

Après l'audit initial :

Présente d'abord un PLAN DE CORRECTION.

Classe les corrections par priorité :

P0 = critique
P1 = important
P2 = amélioration
P3 = optimisation

Puis implémente progressivement.

Après chaque groupe de modifications :

1. tests
2. vérification
3. correction éventuelle
4. résumé.

Ne passe pas à une nouvelle modification si les tests précédents
sont cassés sans expliquer pourquoi.

============================================================
PHASE 21 — AUDIT FINAL
============================================================

Après les modifications :

- relancer les tests
- vérifier les migrations
- vérifier les endpoints
- vérifier les permissions
- vérifier les erreurs
- vérifier les uploads
- vérifier les paiements
- vérifier les performances
- vérifier les logs
- vérifier la configuration production.

Chercher également les régressions.

============================================================
RAPPORT FINAL
============================================================

Produis un rapport avec :

## 1. Résumé

## 2. Problèmes critiques corrigés

## 3. Problèmes importants corrigés

## 4. Sécurité

## 5. Performance

## 6. Base de données

## 7. API

## 8. Monitoring

## 9. Backup/restauration

## 10. Tests

Pour chaque test :

- test
- résultat
- statut PASS/FAIL.

## 11. Fichiers modifiés

Pour chaque fichier :

- chemin
- modification
- raison.

## 12. Problèmes restant à résoudre

Ne cache aucun problème.

## 13. Score de préparation production

Attribue :

Sécurité : /100
Fiabilité : /100
Performance : /100
Scalabilité : /100
Maintenabilité : /100
Observabilité : /100
Backup/Recovery : /100

Puis :

SCORE GLOBAL : /100

Explique précisément les scores.

IMPORTANT :

Ne prétends jamais qu'une protection, un test, un backup ou une
fonctionnalité est opérationnelle si elle n'a pas réellement été
vérifiée.


============================================================
BILAN D'AVANCEMENT — mise à jour 2026-10-07
============================================================

## P0 — Garde-fous de production

- [x] Le démarrage en production refuse `DEBUG=True`
- [x] Le démarrage en production refuse une `SECRET_KEY` faible
- [x] Le démarrage en production refuse SQLite
- [x] Le démarrage en production refuse des réglages `ALLOWED_HOSTS` / HTTPS invalides
- [x] Testé avec une configuration fictive
- [ ] Testé sur un déploiement réel

## P1 — Corrections principales

- [x] Tâches d'abonnement alignées sur les vrais modèles
- [x] Paiements Djomy : séparation brut / frais / net
- [x] Paiements Djomy : validation de la cohérence des montants
- [x] Paiements Djomy : crédit des collectes au montant net
- [x] Conservation de l'ID fournisseur (provider ID)
- [x] Webhooks et callbacks sécurisés
- [x] Uploads validés (taille, type MIME)
- [x] Démarrage Celery corrigé
- [x] Suppression des logs de secrets
- [x] Procédure de restauration documentée
- [x] Contributions possibles après atteinte de la cible
- [x] Contributions bloquées après fermeture manuelle

## P2 — Améliorations locales

- [x] Erreurs d'API ne divulguent plus leurs détails internes
- [x] Listes : `select_related` / `prefetch_related` avant pagination
- [x] Listes : tri appliqué avant pagination
- [x] TLS exigé sur `DATABASE_URL` en production
- [x] `/readyz/` vérifie DB + cache (distinct de `/healthz/`)
- [x] Django mis à niveau
- [x] allauth mis à niveau
- [x] OAuthLib mis à niveau
- [x] Scans de sécurité bloquants dans la CI

## Vérifications effectuées

- [x] 65 tests réussis dans le virtualenv local (`venv/`) avec SQLite et `DEBUG=True`
- [x] `manage.py check` — propre (0 issue identifiée)
- [x] Migrations synchronisées sur SQLite (`showmigrations` tout coché)
- [x] `pip-audit` — aucune vulnérabilité
- [x] Bandit — 0 issue Medium/High (résolu et vérifié)

## À finaliser

- [x] Installer les versions de `requirements.txt` dans le virtualenv local (validé et testé)
- [x] Traiter le P3 résiduel : `accounts/api_urls.py` supprimé, suppression de toute dépendance DRF orpheline
- [x] Réconcilier les anciens paiements : commande `manage.py reconcile_legacy_payments` créée, testée et documentée (support Djomy API, fallback `--assume-zero-fees`, et `--recalculate-funding-totals`)
- [x] Configurer des sauvegardes automatisées et effectuer une restauration réelle : scripts `scripts/backup_db.sh` et `scripts/restore_db.sh` créés, intégrité SHA256 prouvée par test de restauration réelle, et CronJob K8s `k8s/backup-cronjob.yaml` configuré
- [ ] Renseigner et vérifier les secrets et variables (`sync: false`) sur l'hébergement, puis valider les réglages de production déployés
- [ ] Faire tourner les identifiants email / Djomy exposés précédemment et confirmer qu'aucun secret compromis ne reste actif

## Résumé

> Le code P0–P3, les tests automatisés (65 PASS), les scripts d'exploitation
> (sauvegarde/restauration prouvée, réconciliation des paiements) et
> l'environnement dev local (SQLite, DEBUG=True) sont 100% opérationnels.
> Les seules actions restantes concernent la configuration des secrets et
> l'infrastructure de déploiement réel.