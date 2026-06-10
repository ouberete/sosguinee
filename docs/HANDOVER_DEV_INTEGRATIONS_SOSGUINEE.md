# Handover Dev/Infra - Integrations Externes SOS Guinee

## 1) But
Ce guide est fait pour un nouveau developpeur qui rejoint le projet.
Il explique, service par service:
- comment installer
- comment demarrer
- comment appeler depuis le code Python
- comment tester
- comment depanner

---

## 2) Stack des services externes

- `PostgreSQL` (base de donnees prod)
- `Redis` (broker queue)
- `Celery Worker` (execution async)
- `Celery Beat` (planification taches)
- `DJOMY` (paiement)
- `SMTP` (emails)
- `Sentry` (monitoring erreurs)
- `Google OAuth` (authentification sociale)
- `Cloudflare Turnstile` (captcha)

### Important: services dockerises vs services SaaS
- Dockerises dans ce projet: `db`, `redis`, `web`, `celery_worker`, `celery_beat`, `nginx`
- Externes (SaaS) donc non dockerises localement: `DJOMY`, `SMTP provider`, `Google OAuth`, `Turnstile`, `Sentry`
- Les variables de ces services SaaS sont injectees dans les conteneurs via `env_file: .env` dans `docker-compose*.yml`

---

## 3) Setup rapide pour un nouveau dev

## 3.1 Installation Python locale
Le projet installe deja les libs dans Docker. En local (hors Docker), installer aussi:
```bash
pip install -r requirements.txt
pip install "celery[redis]==5.4.0" "sentry-sdk==2.29.1"
```

## 3.2 Variables `.env` minimales (dev)
```env
DEBUG=True
USE_POSTGRES=False
SITE_URL=http://127.0.0.1:8000

# Async
ASYNC_EMAIL_ENABLED=False
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/0

# SMTP
EMAIL_HOST=
EMAIL_PORT=465
EMAIL_USE_SSL=True
EMAIL_USE_TLS=False
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=

# DJOMY
DJOMY_CLIENT_ID=
DJOMY_CLIENT_SECRET=
DJOMY_BASE_URL=https://sandbox-api.djomy.africa/v1
DJOMY_WEBHOOK_SECRET=
```

## 3.3 Démarrage Docker recommandé
```bash
docker compose up -d --build
```

Services lancés:
- `web`
- `db`
- `redis`
- `celery_worker`
- `celery_beat`

Logs:
```bash
docker compose logs -f web
docker compose logs -f celery_worker
docker compose logs -f celery_beat
```

---

## 4) Redis + Celery (comment utiliser)

## 4.1 Où est la config
- `sosguinee/settings.py` (variables `CELERY_*`, `ASYNC_EMAIL_ENABLED`)
- `sosguinee/celery.py`
- `sosguinee/tasks.py`

## 4.2 Comment lancer sans Docker (local)
Terminal 1:
```bash
redis-server
```
Terminal 2:
```bash
celery -A sosguinee worker -l info -Q default,email
```
Terminal 3:
```bash
celery -A sosguinee beat -l info
```

## 4.3 Comment appeler une tache Celery depuis Python
Exemple direct:
```python
from sosguinee.tasks import send_email_task

send_email_task.delay(
    recipient_list=["user@example.com"],
    subject="Sujet test",
    template_path="page/template_email/contact_form_email.html",
    context={"name": "Test"},
)
```

Exemple via service metier (recommande):
```python
from sosguinee.utils.email_service import EmailService

EmailService.send_template_email(
    recipient_list=["user@example.com"],
    subject="Sujet",
    template_path="page/template_email/contact_form_email.html",
    context={"name": "User"},
)
```
Si `ASYNC_EMAIL_ENABLED=True`: queue Celery.  
Sinon: envoi synchro (fallback).

## 4.4 Quand coder une nouvelle tache
1. Ajouter la tache dans `sosguinee/tasks.py`
2. Si besoin, ajouter une route dans `CELERY_TASK_ROUTES` (`settings.py`)
3. Appeler la tache avec `.delay(...)`
4. Surveiller logs worker

---

## 5) SMTP (emails) - utilisation code

## 5.1 Fichier central
- `sosguinee/utils/email_service.py`

## 5.2 Fonctions disponibles
- `send_template_email(...)`
- `send_alert_notification(alert)`
- `send_funding_request_notification(funding_request)`
- `send_donation_notification(donation)`
- `send_subscription_notification(user, context)`
- `send_subscription_reminder(user)`

## 5.3 Exemple dans une vue
```python
EmailService.send_template_email(
    recipient_list=[email],
    subject="Message de contact",
    template_path="page/template_email/contact_form_email.html",
    context={"name": name, "email": email, "message": message},
)
```

## 5.4 Traçabilité
Chaque email est enregistré dans `EmailContent` (`page.models.EmailContent`) avec:
- `is_sent`
- `date_sent`

---

## 6) DJOMY (paiement) - utilisation code

## 6.1 Fichiers utiles
- service DJOMY: `django_djomy/services.py`
- flux paiement: `page/views.py`
- webhook principal: `POST /djomy/webhook/` (`sosguinee/urls.py`)

## 6.2 Initier un paiement dans le code
Exemple (pattern actuel):
```python
from django_djomy.services import DjomyService

ds = DjomyService()
response_data = ds.init_gateway_payment(
    amount=int(amount),
    reference=reference,
    phone=donor_phone,
    country="GN",
    return_url=callback_url,
    cancel_url=cancel_url,
)
payment_url = response_data.get("data", {}).get("redirectUrl")
```

## 6.3 Webhook DJOMY (obligatoire en prod)
Dashboard DJOMY -> webhook URL:
```text
https://<domaine>/djomy/webhook/
```

## 6.4 Bonnes pratiques code paiement
- toujours stocker un `transaction_id` unique local
- toujours vérifier la signature webhook
- traiter webhook de façon idempotente
- logguer les étapes (`payment_event=...`)

---

## 7) Sentry (monitoring) - utilisation

## 7.1 Où c'est branché
- initialisation dans `sosguinee/settings.py` si `SENTRY_DSN` renseigné

## 7.2 Activer
```env
SENTRY_DSN=https://<dsn>@o0.ingest.sentry.io/<project>
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.05
```

## 7.3 Ajouter du contexte métier dans le code
```python
import sentry_sdk

sentry_sdk.set_tag("module", "payment")
sentry_sdk.set_context("transaction", {"reference": reference})
```

---

## 8) Google OAuth (allauth)

## 8.1 Variables
```env
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
```

## 8.2 Où c'est utilisé
- app allauth dans `settings.py`
- routes allauth dans `sosguinee/urls.py`

## 8.3 Checklist dev
1. Configurer redirect URIs dans Google Cloud
2. Vérifier `ALLOWED_HOSTS`/domaine
3. Tester login Google de bout en bout

---

## 9) Turnstile (captcha)

## 9.1 Variables
```env
TURNSTILE_SITE_KEY=
TURNSTILE_SECRET_KEY=
TURNSTILE_VERIFY_URL=https://challenges.cloudflare.com/turnstile/v0/siteverify
```

## 9.2 Où c'est vérifié
- `sosguinee/utils/captcha.py`
- intégré dans les vues/formulaires sensibles (`accounts/views/auth_views.py`, `page/views.py`)

## 9.3 Comportement
- en `DEBUG` sans clé: permissif
- en prod sans clé: rejet

---

## 10) PostgreSQL

## 10.1 Variables
```env
USE_POSTGRES=True
POSTGRES_NAME=sosguinee
POSTGRES_USER=postgres
POSTGRES_PASSWORD=
POSTGRES_HOST=db
POSTGRES_PORT=5432
```

## 10.2 Opérations fréquentes
```bash
python manage.py migrate
python manage.py createsuperuser
```

---

## 11) Flux "ajouter un nouveau service externe"

1. Ajouter variables dans `.env` + `settings.py`
2. Créer un wrapper service dans `sosguinee/utils/` ou app dédiée
3. Ajouter logs métier + gestion erreurs
4. Ajouter retries async si pertinent (Celery)
5. Documenter dans ce fichier
6. Ajouter test de smoke (manuel ou automatisé)

---

## 12) Troubleshooting rapide

## 12.1 Emails non envoyés
- Vérifier logs `celery_worker`
- Vérifier SMTP creds
- Mettre `ASYNC_EMAIL_ENABLED=False` temporairement pour isoler

## 12.2 Paiement bloqué
- Vérifier URL webhook DJOMY
- Vérifier `DJOMY_WEBHOOK_SECRET`
- Vérifier logs `payment_event=...`

## 12.3 Celery ne traite rien
- Vérifier `redis` up
- Vérifier `CELERY_BROKER_URL`
- Vérifier worker connecté à la bonne queue (`default,email`)

## 12.4 Erreurs silencieuses
- Activer `SENTRY_DSN`
- Vérifier logs web + worker

---

## 13) Références internes
- Architecture globale: `docs/ARCHITECTURE_SYSTEME_SOSGUINEE.md`
- Runbook services externes: `docs/RUNBOOK_SERVICES_EXTERNES_SOSGUINEE.md`
