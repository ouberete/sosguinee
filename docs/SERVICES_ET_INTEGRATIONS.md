# Services & intégrations — configuration, appels & débogage

> Pour chaque brique (Djomy, Celery, Redis, emails, Docker, Kubernetes, captcha,
> OAuth, Sentry, stockage objet), ce document explique **comment c'est
> configuré**, **où c'est appelé dans le code** (références `fichier:ligne`), et
> **quoi vérifier pour débugger ou améliorer**. Complète la
> [documentation technique](documentation_technique.md), le
> [guide de prise en main](guide_prise_en_main.md) et l'inventaire des
> [bibliothèques](BIBLIOTHEQUES.md).

## Sommaire
1. [Djomy — paiements](#1-djomy--paiements)
2. [Celery — tâches asynchrones](#2-celery--tâches-asynchrones)
3. [Redis — cache & broker](#3-redis--cache--broker)
4. [Emails — SMTP & backend personnalisé](#4-emails--smtp--backend-personnalisé)
5. [Docker](#5-docker)
6. [Kubernetes](#6-kubernetes)
7. [Stockage objet S3](#7-stockage-objet-s3)
8. [Cloudflare Turnstile — captcha](#8-cloudflare-turnstile--captcha)
9. [django-allauth & Google OAuth](#9-django-allauth--google-oauth)
10. [Sentry — monitoring](#10-sentry--monitoring)
11. [Rate limiting](#11-rate-limiting)

---

## 1. Djomy — paiements

**Rôle** : encaissement des dons et financements (Mobile Money OM/MoMo, carte).

### Configuration (`ensemble224/settings.py:428-434`)
| Variable | Rôle |
|---|---|
| `DJOMY_CLIENT_ID` / `DJOMY_CLIENT_SECRET` | Identifiants API (le `clientSecret` sert aussi à signer le webhook). |
| `DJOMY_BASE_URL` | `https://sandbox-api.djomy.africa/v1` (test) ou `https://api.djomy.africa/v1` (prod). |
| `DJOMY_WEBHOOK_SECRET` | Secret de vérif webhook. **Si vide, on retombe sur `DJOMY_CLIENT_SECRET`** (schéma réel Djomy). |
| `DJOMY_RETURN_URL` / `DJOMY_CANCEL_URL` | Redirections navigateur post-paiement. |
| `DJOMY_REQUEST_TIMEOUT` | Timeout des appels API (défaut 12 s). |

### Où c'est appelé
- **Client API** : `django_djomy/services.py` → classe `DjomyService`
  - `_generate_x_api_key()` : header `X-API-KEY = clientId:HMAC-SHA256(clientSecret, clientId)`.
  - `get_access_token()` : `POST {BASE}/auth` → JWT.
  - `init_gateway_payment(...)` : `POST {BASE}/payments/gateway` (création du lien).
  - `get_payment_status(tx)` : `GET {BASE}/payments/{tx}/status`.
  - `verify_webhook_signature(...)` : HMAC-SHA256(corps, clientSecret), format `v1:<hex>`.
- **Initiation d'un paiement** : `page/views.py` — dons `donation` (~ligne 850,
  appel ~924) et financements `start_djomy_funding_payment` (~ligne 1171,
  appel ~1257) appellent `DjomyService().init_gateway_payment(...)`. En cas
  d'échec d'initiation, l'utilisateur voit le message générique
  `GENERIC_PAYMENT_ERROR` (`page/views.py:51`) ; le détail technique est
  journalisé côté serveur uniquement.
- **Retour navigateur** : `djomy_payment_callback` (`page/views.py:1324`) — ne fait
  **jamais** foi ; il revérifie le statut via l'API (`_verify_payment_status_with_djomy`).
- **Webhook (source de vérité)** : `POST /djomy/webhook/` →
  `page/views.py:djomy_webhook` (~1385). Vérifie la signature
  (`_verify_djomy_webhook_signature`, `page/views.py:346`), puis confirme via
  `_apply_payment_success` (`page/views.py:227` — verrou en base, idempotent,
  crédit du financement, email).
- **Confirmation idempotente** : `_apply_payment_success` est le **seul** point qui
  passe un paiement à « réussi ». Le signal `django_djomy` y délègue aussi
  (`page/signals.py`).
- **URLs** : `ensemble224/urls.py:38` (`/djomy/webhook/`, hors i18n) ; admin de suivi
  dans `django_djomy/urls.py`.

### Débogage
- **Paiement bloqué « en attente »** : le webhook n'a pas atteint le serveur.
  Vérifier dans le dashboard Djomy que l'URL est **`https://<domaine>/djomy/webhook/`**
  (HTTPS, hors préfixe `/fr/`). Tester : `curl -X POST https://<domaine>/djomy/webhook/`
  → doit répondre 401 (signature manquante), pas 404.
- **Webhook rejeté (401)** : signature invalide → vérifier que `DJOMY_WEBHOOK_SECRET`
  vaut le `clientSecret` (ou le laisser vide pour le fallback). Chercher les logs
  `payment_webhook_rejected`.
- **Sandbox au lieu de prod** : `DJOMY_BASE_URL` non défini retombe sur la sandbox.
  Vérifié dans `k8s/configmap.yaml` ; pensez-y aussi sur Render/compose.
- **Traçabilité** : tous les événements sont journalisés via `_log_payment_event`
  (`grep payment_event= <logs>`).

### Robustesse (paiements non aboutis, refresh, double-soumission)
- **Confirmation** uniquement via `_apply_payment_success` (verrou en base,
  idempotent) après API/webhook — jamais sur simple retour navigateur.
- **Refresh de la page de retour** : sans effet (le callback ne retraite que si
  `status == en_attente`, et la confirmation est idempotente).
- **Double-soumission du formulaire** : limitée par le rate limiting
  (5 initiations/h par email ou téléphone).
- **Réconciliation des paiements en attente** (`page/tasks.py:reconcile_pending_payments`,
  job Celery beat) — **désactivée par défaut**. Variables :
  - `PAYMENT_RECONCILIATION_ENABLED` (activer), `PENDING_PAYMENT_EXPIRY_HOURS`
    (délai avant expiration, défaut 24 h), `PAYMENT_RECONCILIATION_EVERY_SECONDS`
    (fréquence, défaut 3600 s). Revérifie via Djomy puis confirme / marque échoué /
    expire les `en_attente` périmés.

### Améliorer
- Mettre en cache le JWT (`get_access_token` est rappelé à chaque requête).
- Consolider à terme sur **un seul** webhook (voir le doublon `django_djomy` vs
  `page.views`, aujourd'hui rendus équivalents).

---

## 2. Celery — tâches asynchrones

**Rôle** : envoi des emails hors requête HTTP + tâches planifiées (rappels/nettoyages).

### Configuration
- **App** : `ensemble224/celery.py` (`Celery("ensemble224")`, autodiscover).
  ⚠️ `DJANGO_SETTINGS_MODULE` y a pour **défaut `ensemble224.settings_dev`** — en prod,
  forcez `ensemble224.settings_prod` via l'environnement (fait dans les manifests K8s
  et `docker-compose.prod.yml`).
- **Réglages** (`ensemble224/settings.py:496-525`) : `CELERY_TASK_ROUTES` (routage vers
  la file `email`), `CELERY_TASK_TIME_LIMIT` / `SOFT_TIME_LIMIT`, `ACKS_LATE`,
  `PREFETCH_MULTIPLIER=1`, et `CELERY_BEAT_SCHEDULE`.
- **Activation** : `ASYNC_EMAIL_ENABLED=True` bascule les emails en asynchrone
  (sinon envoi synchrone dans la requête).

### Où c'est appelé
- **Tâches emails** : `ensemble224/tasks.py` (`send_email_task`,
  `send_donation_notification_task`, etc.) — toutes avec `autoretry_for=(Exception,)`,
  backoff, `max_retries=5`.
- **Mise en file** : `EmailService._queue_task` (`ensemble224/utils/email_service.py:19`)
  appelle `task.delay(...)`. Si le broker est indisponible → **fallback synchrone**
  (log `Queue email indisponible`).
- **Tâches planifiées (beat)** : `accounts/tasks.py`
  (`send_subscription_reminders`, `cleanup_expired_subscriptions`) — schedule dans
  `CELERY_BEAT_SCHEDULE` (quotidien par défaut).
- **Commandes** :
  - worker : `celery -A ensemble224 worker -l info -Q default,email`
  - beat : `celery -A ensemble224 beat -l info` (**1 seule instance**, sinon doublons).

### Débogage
- **Emails ne partent plus** : vérifier que le worker tourne et que Redis répond
  (`kubectl -n ensemble224 logs -f deploy/ensemble224-celery-worker`). En dépannage,
  basculer `ASYNC_EMAIL_ENABLED=False` (envoi synchrone).
- **Rappels en double** : plus d'une réplique `celery-beat`. → `replicas: 1`.
- **Tâche qui tourne trop longtemps** : coupée par `TASK_TIME_LIMIT` (120 s).
- **Inspecter** : `celery -A ensemble224 inspect active` / `... ping`.

### Améliorer
- Séparer les files (`email` déjà routée) si le volume grandit.
- Ajouter Flower pour le monitoring des tâches.

---

## 3. Redis — cache & broker

**Rôle double** : (a) **broker + backend** Celery, (b) **cache** partagé
(rate limiting effectif entre plusieurs pods).

### Configuration (`ensemble224/settings.py:474-493`)
| Variable | Rôle |
|---|---|
| `CELERY_BROKER_URL` | File Celery (défaut `redis://127.0.0.1:6379/0`). |
| `CELERY_RESULT_BACKEND` | Résultats des tâches (défaut = broker). |
| `REDIS_CACHE_URL` | Cache Django (défaut = broker si vide). Base `/1` conseillée. |
| `USE_REDIS_CACHE` | En dev, `True` pour tester le cache Redis (sinon LocMemCache). |

- En **dev** (`DEBUG=True` sans `USE_REDIS_CACHE`) → `LocMemCache` (mémoire process).
- En **prod** → `RedisCache` (django-redis), `KEY_PREFIX="ensemble224"`.

### Où c'est appelé
- **Broker** : implicitement par Celery (cf. §2).
- **Cache / rate limiting** : `from django.core.cache import cache` dans
  `accounts/views/auth_views.py` (ex. `cache.get/add/incr/set`, lignes ~55-65),
  `page/views.py`, `page/services/loss_alert_service.py`.

### Débogage
- **Rate limiting incohérent entre pods** : le cache n'est pas partagé → vérifier
  que `RedisCache` est actif (pas `LocMemCache`) en prod.
- **Connexion refusée** : vérifier l'URL Redis et que le service `redis` tourne
  (`kubectl -n ensemble224 get pods`).
- **Inspecter** : `redis-cli -u $REDIS_CACHE_URL keys 'ensemble224*'`.

### Améliorer
- Séparer physiquement broker (`/0`) et cache (`/1`) — déjà prévu par convention.
- Activer la persistance/HA (Redis managé) pour la prod.

---

## 4. Emails — SMTP & backend personnalisé

### Configuration (`ensemble224/settings.py:331-348`)
- `EMAIL_BACKEND = ensemble224.utils.custom_email_backend.CustomEmailBackend`.
- `EMAIL_HOST/PORT`, `EMAIL_USE_TLS` (587) **ou** `EMAIL_USE_SSL` (465),
  `EMAIL_HOST_USER/PASSWORD`, `EMAIL_CLIENT_DOMAIN` (HELO), `EMAIL_TIMEOUT`.
- `CONTACT_NOTIFY_EMAIL` : destinataire des messages de contact.

### Où c'est appelé
- **Backend** : `ensemble224/utils/custom_email_backend.py` — gère SSL implicite (465)
  vs STARTTLS (587) et un HELO valide (utile chez certains hébergeurs).
- **Service** : `ensemble224/utils/email_service.py` (`EmailService`) — rend le template,
  **enregistre chaque email** dans le modèle `EmailContent` (`is_sent`, `date_sent`),
  et route vers Celery si `ASYNC_EMAIL_ENABLED`.
- **Renvoi des échecs** : commande `python manage.py resend_unsent_emails`.

### Débogage
- **Rien ne part** : hors DEBUG, un warning est loggé si `EMAIL_HOST_USER/PASSWORD`
  manquent (`settings.py:347`). Vérifier le port/protocole (465↔SSL, 587↔TLS).
- **Historique** : table `EmailContent` (admin) → `is_sent=False` = échecs à rejouer.

### Améliorer
- Passer par un service transactionnel (SES, Mailgun) pour la délivrabilité.

---

## 5. Docker

### Fichiers
- **`Dockerfile`** : base `python:3.14-slim`, installe `libpq`, `gettext`,
  `netcat`, puis `requirements.txt`. Entrée = `entrypoint.sh`.
- **`entrypoint.sh`** (mono-conteneur / Fly.io) : `migrate` → `collectstatic` →
  (si `ASYNC_EMAIL_ENABLED`) lance worker + beat en tâche de fond → `gunicorn`.
- **`docker-compose.yml`** : stack de **dev** (web + db + redis…).
- **`docker-compose.prod.yml`** : stack **prod mono-serveur** (nginx + web + celery
  worker + beat + postgres + redis), `DJANGO_SETTINGS_MODULE=settings_prod`.

### Débogage
- **CRLF Windows** : `entrypoint.sh` est « dé-CRLF » dans le Dockerfile (`sed`) —
  sinon crash au démarrage.
- **Logs** : `docker compose logs -f web` / `... celery_worker`.
- Rappel : en K8s les rôles sont **séparés** (web/worker/beat/migrate), pas
  groupés comme dans `entrypoint.sh`.

---

## 6. Kubernetes

**Rôle** : orchestration de production (voir aussi `k8s/README.md` et les guides
[AWS](DEPLOIEMENT_AWS.md) / [OVH](DEPLOIEMENT_OVH.md)).

### Composition (`k8s/`)
| Manifeste | Rôle |
|---|---|
| `configmap.yaml` | Config non sensible (hôtes, DB, Redis, email, S3, Djomy). |
| `secret.example.yaml` | Modèle du Secret `ensemble224-secrets` (clés). |
| `postgres.yaml` | PostgreSQL in-cluster (ou base managée). |
| `redis.yaml` | Redis (broker + cache). |
| `web.yaml` | Django/gunicorn ×2, probes `/healthz/`. |
| `celery-worker.yaml` / `celery-beat.yaml` | Tâches asynchrones / planifiées. |
| `migrate-job.yaml` | Migrations à chaque déploiement (jamais dans le web). |
| `ingress.yaml` | HTTPS (ingress-nginx + cert-manager). Route `/media/user_images/` → web. |
| `hpa.yaml` | Autoscaling du web. |

### Configuration & appels
- Les pods lisent la config via `envFrom` (ConfigMap + Secret) — cf. `web.yaml`.
- `DJANGO_SETTINGS_MODULE=ensemble224.settings_prod` fixé dans la ConfigMap.
- Sonde de vivacité `/healthz/` (`ensemble224/urls.py:healthz`) — **exemptée** de la
  redirection HTTPS (`settings.py:415`).

### Débogage
- **Pod en `Pending`** : souvent un volume/PVC ou une ressource manquante.
- **Probe qui échoue** : le header `Host` des probes (`web.yaml`) doit figurer dans
  `ALLOWED_HOSTS`.
- **Migrations** : relancer le `migrate-job` à chaque déploiement.
- **Commandes** : `kubectl -n ensemble224 get pods -w`,
  `kubectl -n ensemble224 logs -f deploy/ensemble224-web`,
  `kubectl -n ensemble224 exec -it deploy/ensemble224-web -- python manage.py shell`.

---

## 7. Stockage objet S3

**Rôle** : médias (images publiques + pièces d'identité privées). Détaillé dans la
[doc technique §9.4](documentation_technique.md) et les guides
[AWS](DEPLOIEMENT_AWS.md) / [OVH](DEPLOIEMENT_OVH.md).

- **Config** : `USE_S3`, `AWS_*` (2 buckets, clés, région, endpoint) —
  `ensemble224/settings.py`.
- **Code** : `ensemble224/utils/storages.py` (`PublicMediaStorage` /
  `PrivateMediaStorage`). Les pièces d'identité passent par la vue gardée
  `accounts/views/documents.py:protected_user_document`.
- **Débogage** : image publique absente → *bucket policy* du bucket public /
  `AWS_S3_ENDPOINT_URL` ; document privé en 404 → clés `AWS_*` / objet manquant.

---

## 8. Cloudflare Turnstile — captcha

### Configuration (`ensemble224/settings.py:547-551`)
- `TURNSTILE_SITE_KEY`, `TURNSTILE_SECRET_KEY`, `TURNSTILE_VERIFY_URL`.

### Où c'est appelé
- `ensemble224/utils/captcha.py` : `is_turnstile_enabled()`, `verify_turnstile_request()`
  (`POST` vers `.../siteverify`). Utilisé dans `accounts/views/auth_views.py` et
  `page/views.py` (dons/contact) via `_captcha_context()`.

### Débogage
- **Formulaires bloqués en prod** : clés absentes → hors DEBUG,
  `verify_turnstile_request` renvoie « configuration manquante » et **refuse**.
  En DEBUG sans clés, le captcha est **ignoré** (retourne valide).

---

## 9. django-allauth & Google OAuth

### Configuration
- `ensemble224/settings.py` : `AUTHENTICATION_BACKENDS`, `ACCOUNT_LOGIN_METHODS`,
  `ACCOUNT_EMAIL_VERIFICATION='mandatory'`, `SOCIALACCOUNT_PROVIDERS['google']`,
  `SITE_ID=1`.
- La `SocialApp` Google (client id/secret) est stockée **en base** (admin Django),
  pas dans les settings.

### Débogage
- **Erreur redirect_uri** : déclarer `https://<domaine>/accounts/google/login/callback/`
  dans Google Cloud Console.
- **Doublon de provider** : ne pas définir `APP` dans les settings **et** une
  `SocialApp` en base (cf. commentaire `settings.py:103`).
- **`Site` incorrect** : le domaine du `Site` (id=1) doit matcher le domaine réel.

---

## 10. Sentry — monitoring

- **Config** (`ensemble224/settings.py:527-546`) : activé **seulement si** `SENTRY_DSN`
  est défini. `SENTRY_ENVIRONMENT`, `SENTRY_TRACES_SAMPLE_RATE` (0.05 en prod),
  `send_default_pii=False`.
- **Débogage** : pas d'événements ? Vérifier `SENTRY_DSN` et les logs de démarrage
  (`Sentry non initialisé: ...`). Tester avec une exception volontaire.

---

## 11. Rate limiting

**Rôle** : anti-abus sur connexion, reset-password, resend-activation, dons, contact.

- **Mécanisme** : compteurs dans le **cache** (Redis en prod) avec fenêtre glissante —
  `cache.add/incr/set` (ex. `accounts/views/auth_views.py:55-65`).
- **Règle** : ne **pas** remettre les compteurs à zéro après succès pour
  reset-password / resend-activation (anti-spam-relais).

### Débogage
- **Limites inefficaces** en multi-pods : cache non partagé → forcer `RedisCache`
  (cf. §3). En dev `LocMemCache` est par-process (normal).
- Purger un blocage : supprimer la clé correspondante via `redis-cli`.

---

> 🧭 **Règle d'or paiement** (rappel) : un paiement n'est confirmé que par
> `_apply_payment_success` après vérification API Djomy ou webhook signé — jamais
> sur un simple retour navigateur. Toute évolution doit garder `page/tests.py` vert.
