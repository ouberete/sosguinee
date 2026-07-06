# Guide de prise en main — SOS Guinée

> Document de référence pour démarrer sur le projet : architecture, mise en
> route locale, tests, et déploiement (Docker Compose, Fly.io, **Kubernetes**).
> Complète la [documentation technique](documentation_technique.md) et la
> [présentation partenaires](PRESENTATION_PARTENAIRES.md).

---

## 1. Le projet en bref

SOS Guinée est une plateforme solidaire Django permettant de :

- **Signaler des alertes de perte** (personnes disparues, objets, documents) ;
- **Créer des collectes de financement** (santé, urgences, projets
  communautaires) et y contribuer via **Djomy** (Mobile Money OM/MoMo, carte) ;
- **Faire des dons** directs à l'association ;
- Commenter, partager et suivre les demandes (profils utilisateurs).

Bilingue français/anglais (i18n Django), interface Materialize CSS.

## 2. Pile technique

| Couche | Technologie | Version |
|---|---|---|
| Langage | Python | 3.12 → 3.14 |
| Framework | Django | 6.0.x |
| Base de données | PostgreSQL (prod) / SQLite (dev) | 15+ |
| Cache & broker | Redis | 7+ |
| Tâches asynchrones | Celery (worker + beat) | 5.6 |
| Serveur applicatif | Gunicorn + Whitenoise (statiques) | — |
| Auth | django-allauth (email + Google) | 65.x |
| Paiements | Djomy (app locale `django_djomy`) | API v1 |
| Anti-bot | Cloudflare Turnstile | — |
| Monitoring | Sentry (optionnel) | — |
| Admin | django-jazzmin | 3.0.x |

**Applications Django** :

- `page` — cœur métier : alertes, financements, dons, commentaires,
  localisation (Région → Préfecture → Commune → Quartier), journal d'audit ;
- `accounts` — inscription/connexion, activation par email, profils
  (assistant multi-étapes), abonnements (paiement à brancher) ;
- `django_djomy` — client API Djomy (init paiement, statut, signature webhook).

## 3. Arborescence utile

```
sosguinee/
├── sosguinee/            # Projet Django (settings, urls, celery, utils)
│   ├── settings.py       # Configuration commune (env via python-decouple)
│   ├── settings_prod.py  # Force ENVIRONMENT=production, DEBUG=False
│   └── tasks.py          # Tâches Celery (emails)
├── page/                 # App métier (modèles, vues, services, templates)
├── accounts/             # App comptes (vues auth/profil, abonnements)
├── django_djomy/         # Intégration paiement Djomy
├── templates/            # Templates globaux (base.html, emails…)
├── static/               # CSS/JS/images sources
├── locale/               # Traductions fr/en
├── k8s/                  # ★ Manifestes Kubernetes (production)
├── docs/                 # Documentation
├── Dockerfile            # Image applicative (python:3.14-slim)
├── docker-compose.yml    # Dev conteneurisé
├── docker-compose.prod.yml  # Prod mono-serveur (nginx+web+celery+db+redis)
├── entrypoint.sh         # Démarrage conteneur (migrations + gunicorn)
└── requirements.txt      # Dépendances (source unique, -prod/-dev pointent dessus)
```

## 4. Mise en route locale

### 4.1 Prérequis

- Python 3.12+ (3.14 recommandé), Git
- Optionnel : Docker Desktop, Redis local (sinon le cache mémoire suffit en dev)

### 4.2 Installation

```bash
git clone <repo> && cd sosguinee
python -m venv .venv
# Windows : .venv\Scripts\activate   |   Linux/macOS : source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env      # puis ajustez les valeurs
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Le site est sur http://127.0.0.1:8000/ (redirige vers `/fr/`),
l'admin sur http://127.0.0.1:8000/fr/admin/.

### 4.3 Variables d'environnement (`.env`)

Le fichier **`.env.example`** liste tout. Les essentielles :

| Variable | Rôle | Obligatoire en prod |
|---|---|---|
| `SECRET_KEY` | Clé Django — le démarrage **échoue** si absente hors DEBUG | ✅ |
| `DEBUG` / `ENVIRONMENT` | Mode dev/prod | ✅ |
| `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `SITE_URL` | Domaine public | ✅ |
| `POSTGRES_*` ou `DATABASE_URL` | Base de données | ✅ |
| `CELERY_BROKER_URL`, `REDIS_CACHE_URL` | Redis (cache partagé = rate limiting effectif) | ✅ |
| `EMAIL_HOST_USER/PASSWORD` | SMTP (mot de passe d'application) | ✅ |
| `CONTACT_NOTIFY_EMAIL` | Boîte qui reçoit les messages de contact | ✅ |
| `DJOMY_CLIENT_ID/SECRET`, `DJOMY_WEBHOOK_SECRET` | Paiements | ✅ |
| `TURNSTILE_SITE_KEY/SECRET_KEY` | Captcha (désactivé si vide) | recommandé |
| `SENTRY_DSN` | Monitoring erreurs | optionnel |

> ⚠️ **Jamais de `.env` dans git.** Il y a eu un incident : les secrets
> historiques doivent être considérés comme compromis tant que la rotation
> et la purge d'historique n'ont pas été faites.

### 4.4 Tests & qualité

```bash
python manage.py check                 # cohérence de la config
python manage.py makemigrations --check  # aucune migration oubliée
python manage.py test                  # suite de tests (paiements, commentaires…)
```

Les tests de paiement vérifient le contrat de sécurité : un paiement n'est
**jamais** confirmé sur simple retour navigateur — uniquement via l'API
Djomy ou le webhook signé.

### 4.5 i18n

```bash
python manage.py makemessages -l en    # extraire les chaînes
python manage.py compilemessages       # compiler les .po -> .mo
```

## 5. Architecture d'exécution en production

```
                         Internet
                            │ HTTPS
                    ┌───────▼────────┐
                    │ Ingress (TLS)  │  ingress-nginx + cert-manager
                    └───────┬────────┘
                            │
                 ┌──────────▼───────────┐
                 │  web (Deployment ×2) │  gunicorn + whitenoise
                 │  /healthz/ probes    │──────────┐
                 └───┬────────────┬─────┘          │ PVC RWX
                     │            │            ┌───▼────┐
              ┌──────▼───┐   ┌────▼────┐       │ media  │
              │ Postgres │   │  Redis  │       └───▲────┘
              │(StatefulSet)│ │(cache + │           │
              └──────▲───┘   │ broker) │       ┌───┴──────────────┐
                     │       └────▲────┘       │ celery-worker ×1 │ emails
                     │            │            │ celery-beat   ×1 │ tâches cron
                     └────────────┴────────────┴──────────────────┘
```

Rôles séparés (contrairement à `entrypoint.sh` qui groupe tout pour le
mono-conteneur) :

- **web** : HTTP uniquement. `collectstatic` au démarrage, `--workers 3`.
- **celery-worker** : envoi des emails (files `default` + `email`).
- **celery-beat** : rappels d'abonnement, nettoyages. **1 réplique max.**
- **migrate (Job)** : migrations à chaque déploiement, jamais dans le web
  (évite les courses entre répliques).
- **Redis** : indispensable — le rate limiting (connexion, dons, contact)
  repose sur le cache partagé.

## 6. Déploiement Kubernetes (recommandé)

Tous les manifestes sont dans [`k8s/`](../k8s/README.md).

### 6.1 Prérequis cluster

1. Un cluster (managé conseillé : Scaleway Kapsule, OVH MKS, GKE, EKS…)
   et `kubectl` + `kustomize` configurés ;
2. [ingress-nginx](https://kubernetes.github.io/ingress-nginx/) installé ;
3. [cert-manager](https://cert-manager.io) + un `ClusterIssuer`
   `letsencrypt-prod` (TLS automatique) ;
4. Un registre d'images (GHCR, Docker Hub, registre du cloud) ;
5. Un StorageClass **ReadWriteMany** pour le volume media si `web` a
   plusieurs répliques (sinon `replicas: 1`, ou stockage objet S3 à terme).

### 6.2 Construire et pousser l'image

```bash
docker build -t ghcr.io/<org>/sosguinee:v1.0.0 .
docker push ghcr.io/<org>/sosguinee:v1.0.0
```

La même image sert aux 4 rôles (web, worker, beat, migrate) — seule la
commande change.

### 6.3 Adapter les placeholders

Dans `k8s/` remplacez :

- `REGISTRY/sosguinee:latest` → votre image **taguée** (via
  `kustomize edit set image`, voir README k8s) ;
- `sosguinee.example.com` → votre domaine (dans `configmap.yaml`,
  `web.yaml` (probes) et `ingress.yaml`).

### 6.4 Secrets

```bash
kubectl apply -f k8s/namespace.yaml
kubectl -n sosguinee create secret generic sosguinee-secrets \
  --from-literal=SECRET_KEY="$(python -c 'import secrets;print(secrets.token_urlsafe(64))')" \
  --from-literal=POSTGRES_PASSWORD='<fort>' \
  --from-literal=EMAIL_HOST_USER='...' \
  --from-literal=EMAIL_HOST_PASSWORD='...' \
  --from-literal=CONTACT_NOTIFY_EMAIL='...' \
  --from-literal=DJOMY_CLIENT_ID='...' \
  --from-literal=DJOMY_CLIENT_SECRET='...' \
  --from-literal=DJOMY_WEBHOOK_SECRET='...' \
  --from-literal=TURNSTILE_SITE_KEY='...' \
  --from-literal=TURNSTILE_SECRET_KEY='...' \
  --from-literal=SENTRY_DSN=''
```

> GitOps : préférez **SealedSecrets** ou **External Secrets Operator** à un
> Secret en clair.

### 6.5 Déployer

```bash
kubectl apply -k k8s/                       # tout le reste
# migrations (à refaire à CHAQUE déploiement) :
kubectl -n sosguinee delete job sosguinee-migrate --ignore-not-found
kubectl -n sosguinee apply -f k8s/migrate-job.yaml
kubectl -n sosguinee wait --for=condition=complete job/sosguinee-migrate --timeout=300s
kubectl -n sosguinee get pods               # tout doit être Running/Completed
```

Créez le premier admin :

```bash
kubectl -n sosguinee exec -it deploy/sosguinee-web -- python manage.py createsuperuser
```

Pointez le DNS du domaine vers l'IP du LoadBalancer de l'ingress
(`kubectl -n ingress-nginx get svc`), le certificat TLS est émis
automatiquement. Enfin, déclarez le webhook Djomy :
`https://<domaine>/djomy/webhook/`.

### 6.6 Mettre à jour (déploiement continu)

```bash
docker build -t ghcr.io/<org>/sosguinee:v1.0.1 . && docker push ghcr.io/<org>/sosguinee:v1.0.1
cd k8s && kustomize edit set image REGISTRY/sosguinee=ghcr.io/<org>/sosguinee:v1.0.1 && cd ..
kubectl apply -k k8s/                       # rolling update sans coupure
# + relancer le job de migration
```

Retour arrière : `kubectl -n sosguinee rollout undo deploy/sosguinee-web`.

### 6.7 Opérations courantes

| Besoin | Commande |
|---|---|
| Logs web | `kubectl -n sosguinee logs -f deploy/sosguinee-web` |
| Logs worker | `kubectl -n sosguinee logs -f deploy/sosguinee-celery-worker` |
| Shell Django | `kubectl -n sosguinee exec -it deploy/sosguinee-web -- python manage.py shell` |
| État des pods | `kubectl -n sosguinee get pods -w` |
| Redémarrer le web | `kubectl -n sosguinee rollout restart deploy/sosguinee-web` |
| Sauvegarde DB | `kubectl -n sosguinee exec statefulset/postgres -- pg_dump -U sosguinee sosguinee > backup.sql` |
| Santé | `curl -H "Host: <domaine>" http://<ip>/healthz/` → `{"status": "ok"}` |

## 7. Alternatives de déploiement (déjà en place)

### Docker Compose (mono-serveur / VPS)

```bash
cp .env.example .env   # remplir
docker compose -f docker-compose.prod.yml up -d --build
```

Lance nginx (reverse proxy + statiques/media), web, celery worker, beat,
PostgreSQL et Redis sur une machine. Convient à un petit trafic ;
`nginx.conf` doit être complété par du TLS (Certbot ou Cloudflare).

### Fly.io

`fly.toml` + workflow GitHub `deploy.yml` existants : `fly deploy` construit
l'image (l'`entrypoint.sh` y exécute migrations, collectstatic, celery
embarqué et gunicorn dans un seul conteneur).

## 8. Sécurité — règles du projet

1. **Paiements** : ne jamais faire confiance au retour navigateur. La
   confirmation passe par `_apply_payment_success()` (verrou en base,
   idempotent) après vérification API Djomy ou webhook signé (anti-rejeu
   5 min). Toute modification du flux de paiement doit garder les tests
   `page/tests.py` verts.
2. **Secrets** : uniquement en variables d'environnement / Secrets K8s.
   `SECRET_KEY` absente = démarrage refusé hors DEBUG (voulu).
3. **Uploads** : whitelist d'extensions + vérification PIL + taille max.
   Les documents d'identité ne doivent **jamais** entrer dans git.
4. **Rate limiting** : basé sur le cache Redis (partagé entre pods). Ne pas
   remettre les compteurs à zéro après succès pour reset-password /
   resend-activation (anti-spam).
5. **Vues sensibles** : profil et assistant de mise à jour exigent
   l'authentification (`LoginRequiredMixin` / `@login_required`).
6. **En-têtes** : HSTS, nosniff, referrer-policy, cookies Secure/HttpOnly —
   activés automatiquement hors DEBUG.

## 9. Pièges connus (gagnez du temps)

- **Templates en cache** : Django ≥ 4.1 met les templates en cache même en
  DEBUG si le serveur tourne avec `--noreload` → redémarrez le serveur après
  modification d'un template.
- **CSS/JS en cache navigateur** : le stockage statique actuel ne versionne
  pas les fichiers → Ctrl+F5 après un déploiement. (Amélioration possible :
  `CompressedManifestStaticFilesStorage`.)
- **URLs i18n** : presque tout vit sous `/fr/` ou `/en/`. Exceptions hors
  préfixe : `/djomy/webhook/`, `/healthz/`, `/i18n/`.
- **Materialize + flex** : les `.col.s12` ont `margin-left:auto` — dans un
  conteneur flex, ces marges poussent les colonnes à droite. Voir les
  commentaires dans `custom_css.css`.
- **celery-beat** : une seule réplique, sinon emails/rappels en double.
- **`/tmp` du wizard profil** : stockage temporaire multiplateforme via
  `tempfile.gettempdir()` — ne pas remettre un chemin en dur.

## 10. Historique des durcissements (juillet 2026)

Pour comprendre « pourquoi c'est comme ça » : callback de paiement vérifié
côté serveur, webhook anti-rejeu, SECRET_KEY obligatoire, cache Redis,
contact anti-spam-relais, logout en POST, rate limiting anti-spoofing
(X-Forwarded-For), montée Django 5.0→6.0, retrait de `.env`/db/media du
suivi git, protection des vues de profil, anti double-submit paiement,
nettoyage des templates morts. Détail : `git log --oneline` sur la branche
`dev` (commits `43ccc11` → `bf7fbbc`).

> **Actions restant à la charge de l'équipe** :
> 1. rotation de tous les secrets présents dans l'ancien historique git ;
> 2. purge de l'historique (`git filter-repo`) puis force-push coordonné ;
> 3. test de bout en bout d'un paiement en sandbox Djomy ;
> 4. brancher un vrai paiement sur les abonnements (flux désactivé, HTTP 503).
