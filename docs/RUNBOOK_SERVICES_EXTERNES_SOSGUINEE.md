# Runbook - Services Externes SOS Guinee

## 1) Objectif
Ce document explique comment installer, configurer et administrer les services externes relies au projet SOS Guinee.

Services couverts:
- DJOMY (paiement)
- SMTP (emails)
- Redis + Celery (queue et workers)
- Sentry (monitoring erreurs)
- Google OAuth (authentification sociale)
- Cloudflare Turnstile (captcha)
- PostgreSQL (base de donnees en production)

---

## 2) Prerequis generaux

## 2.1 Variables d'environnement
Toutes les configurations passent par `.env` (ou variables injectees en conteneur).

## 2.2 Environnements
- `development`: tests locaux
- `production`: securite stricte, HTTPS, monitoring actif

## 2.3 Verification rapide
```bash
python manage.py check
```

---

## 3) DJOMY (paiement)

## 3.1 Role
DJOMY est le PSP pour:
- dons
- financements de demandes

## 3.2 Variables requises
```env
DJOMY_CLIENT_ID=
DJOMY_CLIENT_SECRET=
DJOMY_BASE_URL=https://sandbox-api.djomy.africa/v1
DJOMY_WEBHOOK_SECRET=
DJOMY_REQUEST_TIMEOUT=12
```

## 3.3 URLs a configurer dans le dashboard DJOMY
- Webhook recommande:
`https://<votre-domaine>/djomy/webhook/`

- Return URL (utilisateur):
les URLs de callback sont generees dynamiquement par le backend.

## 3.4 Procedure de mise en service
1. Creer les credentials DJOMY (sandbox puis production).
2. Renseigner les variables ci-dessus.
3. Configurer le webhook DJOMY vers l'URL du projet.
4. Tester un paiement complet:
- initiation lien
- redirection DJOMY
- callback
- webhook signe
- mise a jour transaction en base

## 3.5 Administration / diagnostic
Verifier:
- logs Django (`payment_event=...`)
- statut des lignes `Donation` et `FundPayment`
- coherence `amount_received` pour `FundingRequest`

Signes d'alerte:
- webhook non recu
- signatures invalides
- transactions en `en_attente` trop longtemps

---

## 4) SMTP (emails transactionnels)

## 4.1 Role
Envoi des emails:
- confirmation abonnement
- notification alerte
- notification financement
- confirmations liees aux paiements

## 4.2 Variables requises
```env
EMAIL_HOST=
EMAIL_PORT=465
EMAIL_USE_TLS=False
EMAIL_USE_SSL=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
EMAIL_CLIENT_DOMAIN=sosguinee.org
EMAIL_TIMEOUT=5
```

Note:
- Port 465 => `EMAIL_USE_SSL=True` et `EMAIL_USE_TLS=False`
- Port 587 => `EMAIL_USE_TLS=True` et `EMAIL_USE_SSL=False`

## 4.3 Procedure de validation
1. Configurer la boite SMTP et ses credentials.
2. Tester un envoi depuis une action metier (ex: contact).
3. Verifier `EmailContent` (`is_sent`, `date_sent`).

## 4.4 Administration
- Surveiller taux d'echec SMTP.
- Renouveler mot de passe applicatif regulierement.
- Verifier SPF/DKIM/DMARC du domaine d'envoi.

---

## 5) Redis + Celery (asynchrone)

## 5.1 Role
Decoupler les traitements longs du cycle HTTP:
- emails via queue
- taches planifiees (rappels abonnement)

## 5.2 Variables requises
```env
ASYNC_EMAIL_ENABLED=True
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
CELERY_TASK_DEFAULT_QUEUE=default
CELERY_TASK_TIME_LIMIT=120
CELERY_TASK_SOFT_TIME_LIMIT=90
CELERY_WORKER_PREFETCH_MULTIPLIER=1
SUBSCRIPTION_REMINDER_EVERY_SECONDS=86400
SUBSCRIPTION_CLEANUP_EVERY_SECONDS=86400
```

## 5.3 Services Docker
Dans les compose:
- `redis`
- `celery_worker`
- `celery_beat`

## 5.4 Commandes d'exploitation
```bash
docker compose up -d redis celery_worker celery_beat web
docker compose logs -f celery_worker
docker compose logs -f celery_beat
```

## 5.5 Administration
Verifier:
- worker up
- beat up
- absence d'accumulation anormale en queue

En cas d'incident:
1. Passer temporairement `ASYNC_EMAIL_ENABLED=False` (fallback sync).
2. Redemarrer worker/redis.
3. Rejouer les emails non envoyes si necessaire.

---

## 6) Sentry (monitoring erreurs)

## 6.1 Role
Capture centralisee des exceptions Django/Celery.

## 6.2 Variables requises
```env
SENTRY_DSN=
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.05
```

## 6.3 Mise en service
1. Creer un projet Sentry.
2. Copier le DSN dans l'environnement.
3. Redemarrer services web/worker.
4. Provoquer une erreur test et verifier la reception dans Sentry.

## 6.4 Administration
- Configurer alertes (email/Slack).
- Definir owners/release tracking.
- Suivre tendances: taux d'erreurs, endpoints impactes, regression.

---

## 7) Google OAuth (allauth)

## 7.1 Role
Connexion via compte Google.

## 7.2 Variables requises
```env
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
```

## 7.3 Configuration Google Cloud
1. Creer un projet.
2. Activer API Google Identity/OAuth.
3. Creer credentials OAuth Web.
4. Ajouter redirect URIs selon domaine:
- local
- preprod/prod

## 7.4 Administration
- Rotation periodique du secret
- Controle des domaines autorises
- Verification des redirections exactes

---

## 8) Cloudflare Turnstile (captcha)

## 8.1 Role
Protection anti-bot des formulaires sensibles.

## 8.2 Variables requises
```env
TURNSTILE_SITE_KEY=
TURNSTILE_SECRET_KEY=
TURNSTILE_VERIFY_URL=https://challenges.cloudflare.com/turnstile/v0/siteverify
```

## 8.3 Mise en service
1. Creer le site dans dashboard Cloudflare Turnstile.
2. Recuperer site key + secret.
3. Renseigner variables.
4. Tester soumission formulaire avec et sans validation captcha.

## 8.4 Administration
- Surveiller taux de challenges bloques
- Ajuster mode Turnstile selon trafic

---

## 9) PostgreSQL (production)

## 9.1 Role
Base principale en production.

## 9.2 Variables requises
```env
USE_POSTGRES=True
POSTGRES_NAME=sosguinee
POSTGRES_DB=sosguinee
POSTGRES_USER=postgres
POSTGRES_PASSWORD=
POSTGRES_HOST=db
POSTGRES_PORT=5432
```

## 9.3 Operations standard
```bash
python manage.py migrate --noinput
python manage.py createsuperuser
```

## 9.4 Administration
- Sauvegardes quotidiennes
- Tests de restauration
- Supervision espace disque/connexions

---

## 10) Checklist d'ouverture production

1. DJOMY prod configure (credentials + webhook).
2. SMTP valide (envoi + delivrabilite SPF/DKIM/DMARC).
3. Redis/Celery actifs et stables.
4. Sentry DSN configure.
5. Turnstile configure.
6. PostgreSQL sauvegardes actives.
7. HTTPS + domaines + CSRF trusted origins verifies.
8. Test end-to-end:
- creation alerte
- demande financement
- don/funding payment
- email de confirmation
- reception webhook

---

## 11) Plan de maintenance recommande

Hebdomadaire:
- verifier erreurs Sentry
- verifier echec emails
- verifier paiements en attente anormale

Mensuel:
- rotation secrets (DJOMY/SMTP/OAuth)
- test reprise incident Redis/Celery
- test restoration backup DB

Trimestriel:
- audit securite configuration externe
- revue des webhooks actifs
- revue quotas/coûts services tiers

