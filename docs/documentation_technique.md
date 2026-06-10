# Documentation Technique Complète — SOS Guinée

> Plateforme solidaire guinéenne pour la gestion des alertes de perte/disparition, des demandes de financement et des dons en ligne.

---

## 1. Vue d'ensemble du projet

SOS Guinée est une application web Django permettant aux citoyens guinéens de :
- Publier et consulter des **alertes de perte/disparition** (personnes, objets, documents).
- Créer et financer des **demandes de financement solidaire** (collectes).
- Effectuer des **dons** via le prestataire de paiement africain **Djomy**.
- Gérer leur **profil utilisateur** et leurs abonnements.

L'objectif de cette architecture est de fiabiliser les paiements, d'assurer une délivrabilité asynchrone des emails et de permettre un monitoring efficace des erreurs en production.

---

## 2. Architecture globale du système

Le système repose sur Django et s'intègre avec plusieurs services externes et composants d'infrastructure.

### Schéma logique
```text
Utilisateur
   |
   v
Nginx (Reverse Proxy & Fichiers Statiques)
   |
   v
Django Web App (Gunicorn)
   |-------------------------------> PostgreSQL (Base de données)
   |
   |-------------------------------> DJOMY API (Init paiement)
   |<------------------------------- DJOMY callback/webhook
   |
   |---- enqueue email task -------> Redis (Broker)
                                     |
                                     v
                                  Celery Worker (Asynchrone)
                                     |
                                     v
                                  Serveur SMTP (Envoi d'emails)

Sentry <----------------------------- Django + Celery (Capture d'exceptions)
```

---

## 3. Stack Technologique & Bibliothèques

### 3.1 Infrastructure & Backend
- **Python** 3.11
- **Django** 6.0.6 (Framework web)
- **PostgreSQL** 15 (Base de données de production)
- **SQLite** (Base de données de développement locale)
- **Gunicorn** 26.0.0 (Serveur WSGI)
- **Celery** 5.4.0 (File de tâches asynchrones)
- **Redis** 7 (Broker de messages pour Celery)
- **Docker & Docker Compose** (Conteneurisation et orchestration)
- **Nginx** (Serveur web)

### 3.2 Frontend
- **Materialize CSS** (Framework CSS)
- **Vanilla JavaScript**
- **Google Material Icons** & **Font Awesome**

### 3.3 Bibliothèques Python Critiques
- `django-allauth` (Authentification et OAuth Google)
- `django-crispy-forms` & `django-formtools` (Rendu UI et formulaires multi-étapes)
- `django-jazzmin` (Interface d'administration)
- `django_djomy` (Intégration du module de paiement)
- `python-decouple` (Gestion des variables d'environnement)
- `sentry-sdk` (Monitoring d'erreurs)
- `pillow` (Traitement d'images)

---

## 4. Architecture & Arborescence du projet

```text
sosguinee/                          ← Racine du projet
├── sosguinee/                      ← Paramètres globaux (settings, urls, celery, wsgi)
├── page/                           ← Application principale (alertes, collectes, UI publique)
│   ├── models.py                   ← Modèles métier (LossAlert, FundingRequest, etc.)
│   ├── views.py                    ← Vues principales
│   ├── services/                   ← Logique métier séparée (services)
│   ├── management/commands/        ← Scripts (load_guinea_locations, etc.)
│   └── data/                       ← Données de seed (localités, référentiels)
├── accounts/                       ← Gestion des utilisateurs et profils
│   ├── models/subscription.py      ← Modèles d'abonnement
│   └── views/profile.py            ← Vues profil multi-étapes
├── django_djomy/                   ← Module de paiement Djomy
├── static/                         ← Fichiers statiques (CSS, JS, Materialize)
├── templates/                      ← Templates HTML (base, accounts, email)
├── locale/                         ← Fichiers de traduction (i18n)
├── docker-compose.yml              ← Stack de développement
├── docker-compose.prod.yml         ← Stack de production
└── requirements.txt                ← Dépendances du projet
```

---

## 5. Modèles de données principaux

### Application `page`
- **Géographie :** `Region` → `Prefecture` → `Commune` → `Quarter`
- **Alertes :** `LossAlert` (liée à `LossAlertType`, `LossAlertStatus`, `User`)
- **Financements :** `FundingRequest` (liée à `FundingType`, `FundingRequestStatus`, `User`)
- **Interactions :** `Donation`, `FundPayment` (liés aux collectes), `Comment`, `MessageContact`

### Application `accounts`
- **Profil :** `UserDetails` (liée en OneToOne à `User`, contient les informations KYC, réseaux sociaux)
- **Abonnement :** `Subscription` (liée à `User`)

### Application `django_djomy`
- **Paiements :** `DjomyTransaction` (Gère l'état de la transaction PSP : pending, success, failed)

---

## 6. Flux de données et d'intégration clés

### 6.1 Paiement (Djomy)
1. L'utilisateur soumet un formulaire de don ou de financement.
2. Django crée une entrée locale (`Donation` ou `FundPayment`).
3. Appel à `init_gateway_payment` du service Djomy.
4. Redirection de l'utilisateur vers l'URL de paiement Djomy.
5. Post-paiement, Djomy effectue deux actions :
   - Redirection navigateur vers le **Callback URL**.
   - Appel serveur à serveur vers le **Webhook URL** (`POST /djomy/webhook/`).
6. Le Webhook vérifie la signature, met à jour le statut du paiement de manière idempotente et déclenche un signal pour envoyer un email.

### 6.2 Envoi d'emails (Asynchrone via Celery)
1. Un événement survient (inscription, paiement validé, etc.).
2. Le backend appelle `EmailService`.
3. Si `ASYNC_EMAIL_ENABLED=True`, la tâche (`send_email_task`) est envoyée dans la queue Redis.
4. Le Celery Worker traite la tâche et envoie l'email via le serveur SMTP.
5. (Fallback) Si l'asynchrone est désactivé, l'envoi se fait de manière synchrone.

### 6.3 Mise à jour du profil (Multi-étapes)
Utilisation de `SessionWizardView` dans `accounts/views/profile.py` :
- **Étape 1 :** `UserInfosForm` (Informations personnelles, adresse avec listes déroulantes en cascade JS).
- **Étape 2 :** `UserDocumentForm` (Upload de pièces d'identité et photos).
- **Étape 3 :** `UserLinkForm` (Réseaux sociaux).
L'enregistrement final se fait dans la méthode `done()`.

---

## 7. Guide d'installation et de démarrage

### 7.1 Démarrage Rapide (Local via Docker - Recommandé)
C'est la méthode la plus simple car elle inclut Redis et Celery.

1. **Préparer l'environnement :**
   ```bash
   cp .env.example .env
   # Configurer les variables essentielles dans .env (cf. Section 8)
   ```

2. **Lancer la stack Docker :**
   ```bash
   docker compose up -d --build
   ```

3. **Initialiser la base de données et les données :**
   ```bash
   docker compose exec web python manage.py migrate
   docker compose exec web python manage.py load_guinea_locations
   docker compose exec web python manage.py load_alert_funding_references
   docker compose exec web python manage.py createsuperuser
   ```

4. **Accéder à l'application :**
   - Web: http://localhost:8000
   - Admin: http://localhost:8000/admin

### 7.2 Démarrage Hors-Docker (Développement classique)
Nécessite d'installer Redis en local si vous testez les files d'attente.

```bash
uv venv
uv pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```
*(Optionnel)* Lancer Celery dans des terminaux séparés :
```bash
celery -A sosguinee worker -l info -Q default,email
celery -A sosguinee beat -l info
```

---

## 8. Configuration des Environnements (Variables `.env`)

Le fichier `.env` contrôle le comportement du système.

### Variables Essentielles
| Variable | Description |
|---|---|
| `ENVIRONMENT` | `development` ou `production` |
| `DEBUG` | `True` (dev) ou `False` (prod) |
| `SECRET_KEY` | Clé cryptographique Django (Obligatoire en prod) |
| `ALLOWED_HOSTS` | Noms de domaine autorisés, ex: `sosguinee.org,www.sosguinee.org` |
| `SITE_URL` | URL de base pour les liens dans les emails (ex: `https://sosguinee.org`) |

### Base de données (PostgreSQL)
| Variable | Description |
|---|---|
| `USE_POSTGRES` | `True` pour utiliser PostgreSQL (défaut). `False` pour SQLite (dev local). |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | Identifiants PostgreSQL. |
| `POSTGRES_HOST`, `POSTGRES_PORT` | `db` et `5432` par défaut en Docker. |

### Djomy (Paiement)
| Variable | Description |
|---|---|
| `DJOMY_CLIENT_ID`, `DJOMY_CLIENT_SECRET` | Identifiants API Djomy. |
| `DJOMY_BASE_URL` | URL de l'API (sandbox ou prod). |
| `DJOMY_WEBHOOK_SECRET` | Secret pour valider la signature des requêtes entrantes. |

### SMTP (Emails)
| Variable | Description |
|---|---|
| `EMAIL_HOST`, `EMAIL_PORT` | Serveur SMTP (ex: `smtp.gmail.com`, Port `465` SSL ou `587` TLS) |
| `EMAIL_USE_SSL`, `EMAIL_USE_TLS` | `True`/`False` selon le port. |
| `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` | Identifiants du compte expéditeur. |

### Celery & Redis (Asynchrone)
| Variable | Description |
|---|---|
| `ASYNC_EMAIL_ENABLED` | `True` pour utiliser la file d'attente, `False` pour synchrone. |
| `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` | ex: `redis://redis:6379/0` (ou `127.0.0.1` hors docker). |

### Sentry, Turnstile, Google OAuth
| Variable | Description |
|---|---|
| `SENTRY_DSN` | URL DSN pour activer le monitoring d'erreurs en production. |
| `TURNSTILE_SITE_KEY`, `TURNSTILE_SECRET_KEY` | Clés Cloudflare Turnstile (CAPTCHA). |
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` | Clés OAuth Google Cloud Console. |

---

## 9. Gestion des Services Externes (Runbook & Handover)

### 9.1 PostgreSQL (Production)
C'est la base de données principale.
- **Opérations :** `python manage.py migrate`
- **Administration :** Planifier des sauvegardes régulières (cron dump).

### 9.2 Redis & Celery
Utilisé pour soulager le processus web des tâches lourdes (envoi d'emails).
- **Monitoring :** Consulter les logs du worker (`docker compose logs -f celery_worker`).
- **Troubleshooting :** Si les emails ne partent plus, vérifier que Redis est accessible et que le worker tourne. En cas de blocage persistant, basculer `ASYNC_EMAIL_ENABLED=False` temporairement.

### 9.3 DJOMY (Paiements)
- **Webhook en production :** Vous devez renseigner `https://<votre-domaine>/djomy/webhook/` dans le dashboard Djomy.
- **Troubleshooting :** Si un paiement reste "en attente" côté Django mais est validé côté banque, c'est que le Webhook n'a pas atteint votre serveur (vérifier DNS, pare-feu, ou configuration du webhook Djomy).

### 9.4 Sentry (Monitoring)
Capture automatiquement toutes les exceptions Python (Django & Celery).
- **Mise en service :** Obtenir le DSN depuis le dashboard Sentry et définir `SENTRY_DSN` et `SENTRY_ENVIRONMENT=production`.

### 9.5 Google OAuth & Cloudflare Turnstile
- **Google OAuth :** Renseigner les "Redirect URIs" dans Google Cloud Console (ex: `https://<domaine>/accounts/google/login/callback/`).
- **Turnstile :** Sans les clés en production, les formulaires protégés (inscription, don) bloqueront les requêtes.

---

## 10. Sécurité & Internationalisation (i18n)

### Sécurité
- **En-têtes HTTP (Prod) :** HSTS, X-Frame-Options: DENY, CSRF & SESSION Cookies Sécurisés.
- **Protection Bot :** Intégration stricte de Cloudflare Turnstile.
- **CSRF :** Renseigner `CSRF_TRUSTED_ORIGINS` avec le domaine de production (ex: `https://sosguinee.org`).

### Internationalisation (i18n)
- Le site supporte le Français (défaut) et l'Anglais.
- Les URLs utilisent `i18n_patterns` (ex: `/fr/alertes/`).
- Commande de traduction : `python manage.py makemessages -l fr` et `python manage.py compilemessages`.

---

## 11. Commandes d'Administration Courantes

```bash
# Charger/Mettre à jour les localités Guinéennes (Idempotent)
python manage.py load_guinea_locations
python manage.py load_guinea_locations --reset # Pour forcer la suppression avant recréation

# Charger les types et statuts de base
python manage.py load_alert_funding_references

# Tenter de renvoyer les emails restés en statut d'échec dans la BDD
python manage.py resend_unsent_emails

# Vider les sessions expirées
python manage.py clearsessions
```

---

## 12. Checklist de Mise en Production

Avant l'ouverture au public, vérifiez impérativement :

1. [ ] `DEBUG=False` dans le fichier `.env`.
2. [ ] `SECRET_KEY` est générée aléatoirement et gardée secrète.
3. [ ] `ALLOWED_HOSTS` et `CSRF_TRUSTED_ORIGINS` contiennent le bon domaine (https).
4. [ ] Paramètres SMTP (`EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`) configurés.
5. [ ] Credentials de production DJOMY en place et **Webhook configuré** sur le dashboard DJOMY.
6. [ ] Redis et Celery Workers lancés et surveillés.
7. [ ] Clés Turnstile configurées (sinon les inscriptions échoueront).
8. [ ] Plan de sauvegarde PostgreSQL actif.
9. [ ] Test "End-to-End" manuel : Inscription → Création Alerte → Demande Financement → Don Djomy réussi → Réception des emails.

---

*Documentation générée en juin 2026 — SOS Guinée*
