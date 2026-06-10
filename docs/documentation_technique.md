# Documentation Technique — SOS Guinée

> Plateforme solidaire guinéenne pour la gestion des alertes de perte/disparition, des demandes de financement et des dons en ligne.

---

## 1. Vue d'ensemble du projet

SOS Guinée est une application web Django permettant aux citoyens guinéens de :
- Publier et consulter des **alertes de perte/disparition** (personnes, objets, documents)
- Créer et financer des **demandes de financement solidaire** (collectes)
- Effectuer des **dons** via le prestataire de paiement africain **Djomy**
- Gérer leur **profil utilisateur** et leurs abonnements

---

## 2. Stack Technologique

### 2.1 Backend

| Technologie | Version | Rôle |
|---|---|---|
| **Python** | 3.11 | Langage principal |
| **Django** | 6.0.6 | Framework web |
| **PostgreSQL** | 15 | Base de données (production) |
| **SQLite** | — | Base de données (développement) |
| **Gunicorn** | 26.0.0 | Serveur WSGI (production) |
| **Celery** | 5.4.0 | File de tâches asynchrones |
| **Redis** | 7 (Alpine) | Broker pour Celery |

### 2.2 Frontend

| Technologie | Rôle |
|---|---|
| **Materialize CSS** | Framework CSS (Material Design) |
| **Vanilla JavaScript** | Logique côté client (sans framework JS) |
| **Google Material Icons** | Icônes UI |
| **Font Awesome** | Icônes admin |

### 2.3 Infrastructure & Déploiement

| Technologie | Rôle |
|---|---|
| **Docker** | Conteneurisation |
| **Docker Compose** | Orchestration multi-services |
| **Nginx** | Reverse proxy / service des fichiers statiques |
| **Whitenoise** | Service des fichiers statiques via Django |
| **Heroku** | Plateforme cloud alternative (Procfile présent) |

---

## 3. Bibliothèques Python utilisées

### Bibliothèques de production (`requirements-prod.txt`)

| Bibliothèque | Version | Usage |
|---|---|---|
| `django-allauth` | 65.18.0 | Authentification sociale (Google OAuth) et gestion des comptes |
| `django-crispy-forms` | 2.6 | Rendu de formulaires Django avec le template Materialize |
| `django-formtools` | 2.6.1 | Formulaires multi-étapes (`SessionWizardView`) pour la mise à jour du profil |
| `django-jazzmin` | 3.0.4 | Interface d'administration Django modernisée |
| `django-heroku` | 0.3.1 | Compatibilité Heroku |
| `dj-database-url` | 3.1.2 | Parsing d'URL de base de données |
| `pillow` | 12.2.0 | Traitement et compression des images uploadées |
| `python-decouple` | 3.8 | Gestion des variables d'environnement (`.env`) |
| `psycopg2-binary` | 2.9.12 | Adaptateur PostgreSQL pour Django |
| `gunicorn` | 26.0.0 | Serveur WSGI de production |
| `whitenoise` | 6.12.0 | Service des fichiers statiques |
| `social-auth-app-django` | 5.9.0 | Authentification sociale (couche complémentaire) |
| `PyJWT` | 2.13.0 | Gestion des tokens JWT |
| `cryptography` | 48.0.0 | Cryptographie (utilisée par allauth/OAuth) |
| `requests` | 2.34.2 | Appels HTTP sortants (API Djomy, Turnstile) |

### Bibliothèques optionnelles (installées dans le Dockerfile)

| Bibliothèque | Version | Usage |
|---|---|---|
| `celery[redis]` | 5.4.0 | Queue de tâches asynchrones (emails, notifications) |
| `sentry-sdk` | 2.29.1 | Monitoring d'erreurs en production |

---

## 4. Applications Django (INSTALLED_APPS)

```
INSTALLED_APPS = [
    "jazzmin",            # Admin UI
    "django.contrib.admin",
    "django.contrib.auth",
    ...
    "accounts",           # App utilisateurs/profils
    "page",               # App principale (alertes, financements, dons)
    "allauth",            # Authentification
    "allauth.socialaccount.providers.google",
    "formtools",          # Formulaires multi-étapes
    "crispy_forms",
    "django_djomy",       # Intégration paiement Djomy
]
```

---

## 5. Architecture & Arborescence du projet

```
sosguinee/                          ← Racine du projet
│
├── 📁 sosguinee/                   ← Configuration Django (package projet)
│   ├── settings.py                 ← Paramètres principaux (toutes les configs)
│   ├── settings_dev.py             ← Surcharge paramètres dev
│   ├── settings_prod.py            ← Surcharge paramètres prod
│   ├── urls.py                     ← URLs racine avec i18n_patterns
│   ├── celery.py                   ← Configuration Celery
│   ├── tasks.py                    ← Tâches Celery (emails, notifications)
│   ├── wsgi.py                     ← Point d'entrée WSGI
│   ├── asgi.py                     ← Point d'entrée ASGI
│   └── utils/
│       └── custom_email_backend.py ← Backend email personnalisé
│
├── 📁 page/                        ← Application principale
│   ├── models.py                   ← Tous les modèles métier (34 KB)
│   ├── views.py                    ← Toutes les vues (64 KB)
│   ├── forms.py                    ← Formulaires (LossAlert, FundingRequest, Donation...)
│   ├── admin.py                    ← Configuration admin Jazzmin (17 KB)
│   ├── urls.py                     ← Routes URL de l'application
│   ├── api_urls.py                 ← Routes API REST (localités cascadées)
│   ├── signals.py                  ← Signaux Django (post_save, etc.)
│   ├── middleware.py               ← CurrentUserMiddleware
│   ├── tests.py                    ← Tests unitaires
│   ├── 📁 services/                ← Couche service (logique métier)
│   │   ├── funding_request_service.py
│   │   └── loss_alert_service.py
│   ├── 📁 management/commands/     ← Commandes Django personnalisées
│   │   ├── load_guinea_locations.py       ← Charge les localités (JSON/CSV)
│   │   ├── load_alert_funding_references.py ← Charge les types/statuts
│   │   └── resend_unsent_emails.py        ← Renvoi des emails non envoyés
│   ├── 📁 data/                    ← Données de seed
│   │   ├── guinea_locations.json   ← 8 régions, 33+ préfectures, 200+ communes
│   │   └── default_alert_funding_references.json ← Types/statuts
│   ├── 📁 templates/page/          ← Templates HTML de l'application
│   │   ├── index.html              ← Page d'accueil
│   │   ├── loss_alerts.html        ← Liste des alertes
│   │   ├── loss_alert_details.html ← Détail d'une alerte
│   │   ├── add_loss_alert.html     ← Création d'alerte
│   │   ├── funding_requests.html   ← Liste des collectes
│   │   ├── funding_request_details.html
│   │   ├── add_funding_request.html
│   │   ├── funding_payment.html    ← Page de paiement Djomy
│   │   ├── donation.html           ← Page de don
│   │   ├── contact.html
│   │   ├── about.html
│   │   ├── thanks_payment.html     ← Confirmation paiement
│   │   ├── donation_thanks.html
│   │   ├── 📁 template_email/      ← Templates d'emails transactionnels
│   │   ├── 📁 confirmation_page/   ← Pages de confirmation actions
│   │   ├── 📁 help_policy/         ← Pages légales/aide
│   │   ├── 📁 components/          ← Composants réutilisables
│   │   └── 📁 includes/            ← Inclusions partielles
│   └── 📁 templatetags/            ← Filtres de templates personnalisés
│       └── custom_filters.py       ← format_fr, chip_class, etc.
│
├── 📁 accounts/                    ← Application gestion des utilisateurs
│   ├── forms.py                    ← UserInfosForm, UserDocumentForm, UserLinkForm (28 KB)
│   ├── admin.py                    ← Admin des utilisateurs
│   ├── urls.py                     ← Routes URL accounts
│   ├── api_urls.py                 ← API REST accounts
│   ├── utils.py                    ← Utilitaires accounts
│   ├── tasks.py                    ← Tâches Celery (abonnements)
│   ├── 📁 models/                  ← Modèles utilisateur
│   │   ├── __init__.py
│   │   └── subscription.py        ← Modèle Abonnement
│   ├── 📁 views/                   ← Vues accounts
│   │   ├── auth_views.py           ← Inscription, connexion, activation
│   │   ├── profile.py              ← Profil + UpdateUserProfileWizard
│   │   └── subscription_views.py   ← Gestion des abonnements
│   ├── 📁 management/              ← Commandes accounts
│   └── 📁 templates/accounts/      ← Templates accounts
│       ├── login.html
│       ├── signup.html
│       ├── profil.html             ← Dashboard profil utilisateur
│       ├── user_infos.html         ← Étape 1 : infos personnelles
│       ├── user_document.html      ← Étape 2 : pièce d'identité
│       └── user_link.html          ← Étape 3 : réseaux sociaux
│
├── 📁 django_djomy/                ← Module d'intégration paiement Djomy
│   ├── models.py                   ← Modèles de transaction
│   ├── services.py                 ← Appels API Djomy (5.8 KB)
│   ├── views.py                    ← Vue paiement + webhook
│   ├── urls.py                     ← Routes /djomy/...
│   └── signals.py                  ← Signaux post-paiement
│
├── 📁 static/                      ← Fichiers statiques sources
│   ├── 📁 css/
│   │   └── custom_css.css          ← Styles personnalisés globaux
│   ├── 📁 js/
│   │   ├── index.js                ← JS page d'accueil
│   │   ├── loss_alerts.js          ← JS liste alertes (filtres, AJAX)
│   │   ├── funding_requests.js     ← JS collectes (filtres, AJAX)
│   │   ├── location_cascade.js     ← Cascades Région→Préfecture→Commune→Quartier
│   │   ├── payment_amount_presets.js ← Préréglages montant paiement
│   │   ├── upload_dropzones.js     ← Upload de fichiers glisser-déposer
│   │   └── comments.js             ← Système de commentaires AJAX
│   ├── 📁 materialize/             ← Framework Materialize CSS/JS
│   ├── 📁 profil/                  ← Scripts JS du profil
│   └── 📁 img/                     ← Images statiques
│
├── 📁 templates/                   ← Templates globaux
│   ├── base.html                   ← Template de base (héritage)
│   └── 📁 accounts/
│       └── profile.html            ← (legacy)
│
├── 📁 locale/                      ← Traductions i18n
│   ├── 📁 fr/LC_MESSAGES/          ← Traductions françaises
│   └── 📁 en/LC_MESSAGES/          ← Traductions anglaises
│
├── 📁 media/                       ← Fichiers uploadés (dev)
├── 📁 mediafiles/                  ← Fichiers uploadés (prod)
├── 📁 staticfiles/                 ← Fichiers statiques collectés
│
├── 📁 docs/                        ← Documentation existante
│
├── Dockerfile                      ← Image Docker Python 3.11-slim
├── docker-compose.yml              ← Stack complète (web+db+redis+celery+nginx)
├── docker-compose.prod.yml         ← Variante production
├── nginx.conf                      ← Configuration Nginx reverse proxy
├── entrypoint.sh                   ← Script d'init Docker (migrate, collectstatic...)
├── Procfile                        ← Config Heroku (gunicorn)
├── manage.py                       ← CLI Django
├── requirements.txt                ← Dépendances complètes
├── requirements-prod.txt           ← Dépendances de production
├── requirements-dev.txt            ← Dépendances de développement
├── runtime.txt                     ← Version Python pour Heroku
├── .env.example                    ← Template variables d'environnement
└── .gitignore
```

---

## 6. Modèles de données principaux

### Application `page`

```
Region → Prefecture → Commune → Quarter
  (Hiérarchie géographique de Guinée)

LossAlert                    FundingRequest
  ├── loss_alert_type          ├── funding_request_type
  ├── status (LossAlertStatus) ├── status (FundingRequestStatus)
  ├── region/prefecture/...    ├── region/prefecture/...
  ├── principal_image          ├── principal_image
  ├── optional_docs            ├── optional_docs
  └── user (auth.User)         └── user (auth.User)

Donation                     FundPayment
  └── (don libre)              └── funding_request (FK→FundingRequest)

Comment → (LossAlert ou FundingRequest)
MessageContact
EmailContent (templates d'emails)
```

### Application `accounts`

```
UserDetails (profil étendu)
  ├── user (OneToOne→auth.User)
  ├── photo, id_card (fichiers)
  ├── birth_date, birth_city, nationality
  ├── region/prefecture/commune/quarter (FK géographie)
  ├── address, actual_city, zip_code
  ├── profession, activity_sector, high_education
  ├── facebook, twitter, linkedin, instagram
  ├── bio, person_contact
  └── account_status

Subscription
  ├── user (FK→auth.User)
  ├── plan, status
  └── start_date, end_date
```

### Application `django_djomy`

```
DjomyTransaction
  ├── reference
  ├── amount, currency
  ├── status (pending/success/failed)
  └── metadata JSON
```

---

## 7. Flux de données clés

### 7.1 Paiement (Djomy)

```
Utilisateur → funding_payment.html
  → POST djomy_funding_public (page/views.py)
    → django_djomy/services.py → API Djomy (sandbox/prod)
      → Redirection vers page de paiement Djomy
        → Webhook djomy/webhook/ (callback Djomy)
          → Mise à jour FundPayment.status
            → Email de confirmation (Celery)
```

### 7.2 Envoi d'emails (asynchrone)

```
Action utilisateur (nouvelle alerte, don, etc.)
  → Signal Django (page/signals.py)
    → sosguinee/tasks.py (Celery task)
      → sosguinee/utils/custom_email_backend.py
        → SMTP (Gmail ou autre)
```

### 7.3 Mise à jour du profil (multi-étapes)

```
accounts/views/profile.py → UpdateUserProfileWizard (SessionWizardView)
  Étape 1 : user_infos.html → UserInfosForm  (infos personnelles + cascade localités)
  Étape 2 : user_document.html → UserDocumentForm (photo, pièce d'identité)
  Étape 3 : user_link.html → UserLinkForm (réseaux sociaux, bio)
  → done() → UserDetails.save()
```

---

## 8. Configuration des environnements

### Variables d'environnement (`.env`)

| Variable | Obligatoire prod | Description |
|---|---|---|
| `SECRET_KEY` | ✅ | Clé secrète Django |
| `ENVIRONMENT` | ✅ | `development` ou `production` |
| `DEBUG` | — | `True`/`False` |
| `ALLOWED_HOSTS` | ✅ | Noms d'hôtes autorisés (séparés par virgule) |
| `USE_POSTGRES` | — | Active PostgreSQL (défaut: `True`) |
| `POSTGRES_NAME` | ✅ | Nom de la BDD PostgreSQL |
| `POSTGRES_USER` | ✅ | Utilisateur PostgreSQL |
| `POSTGRES_PASSWORD` | ✅ | Mot de passe PostgreSQL |
| `POSTGRES_HOST` | — | Hôte BDD (défaut: `db`) |
| `EMAIL_HOST` | ✅ | Serveur SMTP |
| `EMAIL_HOST_USER` | ✅ | Compte email expéditeur |
| `EMAIL_HOST_PASSWORD` | ✅ | Mot de passe email |
| `SITE_URL` | ✅ | URL publique du site |
| `DJOMY_CLIENT_ID` | ✅ | ID client API Djomy |
| `DJOMY_CLIENT_SECRET` | ✅ | Secret HMAC Djomy |
| `DJOMY_BASE_URL` | — | URL API Djomy |
| `DJOMY_WEBHOOK_SECRET` | ✅ | Secret vérification webhook |
| `CELERY_BROKER_URL` | — | URL Redis pour Celery |
| `ASYNC_EMAIL_ENABLED` | — | Emails via Celery (`True`/`False`) |
| `TURNSTILE_SITE_KEY` | — | Clé publique Cloudflare Turnstile |
| `TURNSTILE_SECRET_KEY` | — | Clé secrète Turnstile |
| `SENTRY_DSN` | — | DSN Sentry pour monitoring |
| `CSRF_TRUSTED_ORIGINS` | ✅ | Origines CSRF autorisées |

---

## 9. Sécurité

- **CAPTCHA** : Cloudflare Turnstile sur les formulaires publics (connexion, inscription, dons)
- **Authentification** : django-allauth avec vérification email obligatoire
- **OAuth** : Google OAuth 2.0 via allauth
- **En-têtes HTTP** (production) : HSTS, X-Frame-Options: DENY, CSRF_COOKIE_SECURE, SESSION_COOKIE_SECURE, SECURE_CONTENT_TYPE_NOSNIFF
- **Validation de mots de passe** : Longueur minimale 12 caractères, similarité, mots communs
- **Middleware** : `CsrfViewMiddleware`, `SecurityMiddleware`
- **Gestion des secrets** : `python-decouple` + `.env` (jamais committé)
- **Monitoring d'erreurs** : Sentry SDK (optionnel, configuré via `SENTRY_DSN`)

---

## 10. Internationalisation (i18n)

- **Langues supportées** : Français (`fr`) — langue par défaut, Anglais (`en`)
- **Moteur** : Django gettext (`USE_I18N = True`)
- **URLs préfixées** : `i18n_patterns()` — ex: `/fr/alertes/`, `/en/alerts/`
- **Fichiers de traduction** : `locale/fr/LC_MESSAGES/django.po`
- **Script de gestion** : `manage-i18n.ps1` (PowerShell)

---

## 11. Infrastructure Docker (Production)

```yaml
Services:
  nginx          ← Reverse proxy, sert les fichiers statiques (port 80)
  web            ← Application Django via Gunicorn (port 8000 interne)
  db             ← PostgreSQL 15
  redis          ← Redis 7 (broker Celery)
  celery_worker  ← Worker Celery (queues: default, email)
  celery_beat    ← Scheduler Celery (tâches périodiques)

Volumes persistants:
  pgdata         ← Données PostgreSQL
  static_volume  ← Fichiers statiques collectés
  media_volume   ← Fichiers uploadés
```

---

## 12. Commandes de gestion personnalisées

| Commande | Description |
|---|---|
| `python manage.py load_guinea_locations` | Charge/met à jour les localités de Guinée depuis `page/data/guinea_locations.json` (idempotent) |
| `python manage.py load_guinea_locations --reset` | Réinitialise et recharge toutes les localités |
| `python manage.py load_guinea_locations --dry-run` | Simule le chargement sans écrire en base |
| `python manage.py load_alert_funding_references` | Charge les types/statuts d'alertes et de financements |
| `python manage.py load_alert_funding_references --reset` | Réinitialise les référentiels |
| `python manage.py resend_unsent_emails` | Renvoi les emails en échec |
| `python manage.py makemessages -l fr` | Génère les fichiers de traduction |
| `python manage.py compilemessages` | Compile les traductions |

---

## 13. Démarrage rapide (développement)

```bash
# 1. Cloner le projet
git clone <repo>
cd sosguinee

# 2. Créer l'environnement virtuel et installer les dépendances
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt

# 3. Configurer les variables d'environnement
cp .env.example .env
# → Éditer .env avec les valeurs appropriées

# 4. Appliquer les migrations
python manage.py migrate

# 5. Charger les données initiales
python manage.py load_guinea_locations
python manage.py load_alert_funding_references

# 6. Créer un superutilisateur
python manage.py createsuperuser

# 7. Lancer le serveur
python manage.py runserver
# → http://127.0.0.1:8000
# → http://127.0.0.1:8000/admin (interface admin Jazzmin)
```

### Avec uv (recommandé)
```bash
uv run py manage.py runserver
```

---

## 14. Démarrage en production (Docker)

```bash
# 1. Configurer .env avec les variables de production

# 2. Construire et lancer tous les services
docker-compose up --build -d

# 3. Initialiser la base de données (première fois)
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py load_guinea_locations
docker-compose exec web python manage.py load_alert_funding_references
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py collectstatic --no-input
```

---

## 15. Tests

```bash
# Lancer les tests unitaires
python manage.py test page
python manage.py test accounts
```

Les tests sont situés dans :
- [`page/tests.py`](file:///d:/Projets/Web/SOS%20GUINEE/sosguinee/page/tests.py)
- [`accounts/tests.py`](file:///d:/Projets/Web/SOS%20GUINEE/sosguinee/accounts/tests.py)

---

*Documentation générée le 10 juin 2026 — SOS Guinée*
