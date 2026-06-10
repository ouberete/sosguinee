# Documentation Technique - SOS Guinee

## 1) Objectif du document
Ce document explique l'architecture globale de SOS Guinee et les outils critiques ajoutes pour fiabiliser:
- les envois d'emails
- les paiements (don et financement) via DJOMY
- le monitoring applicatif

Il sert de reference pour developpeurs, ops et administration.

---

## 2) Architecture globale du systeme

### Vue d'ensemble
Le systeme repose sur Django et se compose de:
- Frontend web (templates Django + JS)
- Backend Django (logique metier, API, securite)
- Base de donnees (PostgreSQL en prod, SQLite en local selon config)
- Paiement externe DJOMY
- Queue asynchrone (Celery + Redis)
- Monitoring erreurs (Sentry, optionnel)

### Schema logique
```text
Utilisateur
   |
   v
Nginx (prod)
   |
   v
Django Web App
   |-------------------------------> PostgreSQL
   |
   |-------------------------------> DJOMY API (init paiement)
   |<------------------------------- DJOMY callback/webhook
   |
   |---- enqueue email task -------> Redis (broker)
                                     |
                                     v
                                  Celery Worker
                                     |
                                     v
                                  SMTP provider

Sentry <----------------------------- Django + Celery (exceptions)
```

---

## 3) Composants et outils

## 3.1 Django (coeur applicatif)
- Gerer les formulaires (alertes, demandes de financement, dons, contact)
- Gerer les permissions utilisateur
- Gerer les callbacks/webhooks DJOMY
- Enregistrer les traces metier (paiements, actions utilisateur)

## 3.2 DJOMY (paiement)
- Service: `django_djomy/services.py`
- Initialisation gateway: creation d'un lien de paiement
- Callback navigateur: retour utilisateur apres paiement
- Webhook serveur-a-serveur: confirmation fiable du statut
- Signature webhook verifiee cote backend

## 3.3 Broker + workers (Celery + Redis)
- Redis: transport de messages
- Celery worker: execute les taches asynchrones (emails)
- Celery beat: planification des taches periodiques (rappels abonnement)
- Mode fallback prevu: si queue indisponible, email synchro

## 3.4 Monitoring
- Sentry (optionnel): capture des erreurs runtime Django/Celery
- Logs applicatifs: evenements paiement traces dans les logs backend

---

## 4) Flux fonctionnels critiques

## 4.1 Don / financement via DJOMY
1. L'utilisateur soumet le formulaire de paiement.
2. Django cree une transaction locale (`Donation` ou `FundPayment`).
3. Django appelle DJOMY `init_gateway_payment`.
4. DJOMY retourne `redirectUrl`.
5. L'utilisateur est redirige vers la page DJOMY.
6. DJOMY notifie ensuite:
- callback utilisateur (navigateur)
- webhook serveur (source de verite technique)
7. Le backend met a jour statut et montants de maniere idempotente.

## 4.2 Envoi d'emails
1. Le backend appelle `EmailService`.
2. Si `ASYNC_EMAIL_ENABLED=True`, la tache part en queue Celery.
3. Le worker envoie l'email via SMTP.
4. Le statut d'envoi est enregistre dans `EmailContent`.
5. En cas d'echec queue, fallback synchro possible.

---

## 5) Endpoints DJOMY utiles

## 5.1 Endpoint webhook principal (recommande)
- `POST /djomy/webhook/`
- Defini dans `sosguinee/urls.py`
- Avantage: URL stable hors i18n

## 5.2 Callback retour utilisateur
- `GET /<lang>/djomy/callback/<payment_id>/<type>/`
- Utilise pour l'experience utilisateur post-paiement

## 5.3 Endpoint historique dans module `django_djomy`
- `POST /<lang>/webhooks/djomy/`
- Present via `django_djomy/urls.py`
- Recommandation: standardiser vers `/djomy/webhook/` pour la prod

---

## 6) Configuration environnement

Variables principales:
- `DJOMY_CLIENT_ID`
- `DJOMY_CLIENT_SECRET`
- `DJOMY_BASE_URL`
- `DJOMY_WEBHOOK_SECRET`
- `DJOMY_REQUEST_TIMEOUT`

- `ASYNC_EMAIL_ENABLED`
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`

- `SENTRY_DSN`
- `SENTRY_ENVIRONMENT`
- `SENTRY_TRACES_SAMPLE_RATE`

- `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`

Exemple local:
```env
ASYNC_EMAIL_ENABLED=False
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/0
SENTRY_DSN=
```

---

## 7) Exploitation et commandes

## 7.1 Verification Django
```bash
python manage.py check
```

## 7.2 Lancer en Docker (avec Redis + Celery)
```bash
docker compose up -d --build
```

Services cibles:
- `web`
- `redis`
- `celery_worker`
- `celery_beat`

## 7.3 Logs utiles
```bash
docker compose logs -f web
docker compose logs -f celery_worker
docker compose logs -f celery_beat
```

---

## 8) Fiabilite et securite

Mesures en place:
- Verification signature webhook DJOMY
- Idempotence sur traitement webhook/callback
- Controle anti-spam sur formulaires (rate-limit + captcha)
- Taches asynchrones avec retry Celery
- Journalisation evenements de paiement

Recommandations complementaires:
- Garder un endpoint webhook unique en prod
- Forcer HTTPS partout (deja prevu cote settings/proxy)
- Mettre alerting Sentry en environnement production

---

## 9) Checklist de mise en production

1. Renseigner toutes les variables DJOMY et SMTP.
2. Configurer le webhook DJOMY vers:
- `https://<votre-domaine>/djomy/webhook/`
3. Activer queue email:
- `ASYNC_EMAIL_ENABLED=True`
4. Verifier que Redis + Celery worker + Celery beat sont demarres.
5. Configurer `SENTRY_DSN`.
6. Tester un paiement bout en bout:
- creation transaction
- redirection DJOMY
- callback
- webhook
- email
- mise a jour statut/metriques

---

## 10) Notes implementation actuelle

- Le projet contient deja les points d'integration Celery/Sentry dans `settings.py`.
- Les taches asynchrones email sont dans `sosguinee/tasks.py`.
- Le service email central est `sosguinee/utils/email_service.py`.
- Les traces paiements sont loggees avec le prefixe `payment_event=...` dans les logs backend.

---

## 11) Evolution recommandee (phase 2)

Pour monter en robustesse:
- Dashboard Prometheus/Grafana (latence webhook, taux echec email)
- DLQ (dead-letter queue) pour echec permanent
- Reconciliation automatique des paiements en echec/timeout

