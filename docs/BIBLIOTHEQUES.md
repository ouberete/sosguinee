# Bibliothèques & dépendances — SOS Guinée

> Inventaire complet des bibliothèques du projet : dépendances **directes**
> (déclarées dans `requirements.txt`) et **transitives** (tirées automatiquement
> par pip), avec leur rôle et leur version verrouillée. Complète la
> [documentation technique](documentation_technique.md).

## 1. Gestion des dépendances

- **Source unique** : `requirements.txt` liste les dépendances **directes**.
- `requirements-dev.txt` et `requirements-prod.txt` pointent tous deux dessus
  (`-r requirements.txt`) — pas de divergence dev/prod côté paquets.
- Les versions ci-dessous correspondent à l'environnement verrouillé (voir
  l'annexe §4, `pip freeze`).

Installation :

```bash
pip install -r requirements.txt          # ou requirements-prod.txt
```

Régénérer la liste verrouillée complète :

```bash
pip freeze > docs/_pip-freeze.txt        # référence de reproductibilité
```

---

## 2. Dépendances directes (`requirements.txt`)

| Bibliothèque | Version | Rôle dans le projet |
|---|---|---|
| **Django** | 6.0.6 | Framework web (ORM, vues, admin, i18n, sécurité). |
| **django-allauth**`[socialaccount]` | 65.18.0 | Authentification email + connexion **Google** (OAuth2). |
| **django-crispy-forms** | 2.6 | Rendu des formulaires (pack `materialize`). |
| **django-formtools** | 2.6.1 | Formulaires multi-étapes (assistant de profil, `SessionWizardView`). |
| **django-jazzmin** | 3.0.5 | Thème de l'interface d'administration. |
| **django-redis** | 7.0.0 | Backend de cache Redis (rate limiting partagé entre pods). |
| **dj-database-url** | 3.1.2 | Configuration BD via `DATABASE_URL` (Render/RDS/OVH Managed DB). |
| **python-decouple** | 3.8 | Lecture des variables d'environnement (`.env`). |
| **whitenoise** | 6.12.0 | Service des fichiers **statiques** par l'app (sans nginx dédié). |
| **gunicorn** | 26.0.0 | Serveur d'application WSGI (production). |
| **psycopg2-binary** | 2.9.12 | Pilote PostgreSQL. |
| **django-storages** | 1.14.6 | Stockage des **médias** sur S3 / Object Storage (AWS S3, OVH). |
| **boto3** | 1.40.44 | SDK AWS/S3 utilisé par django-storages. |
| **pillow** | 12.3.0 | Traitement d'images (`ImageField`, validation des uploads). |
| **requests** | 2.34.2 | Client HTTP (appels à l'**API Djomy**, Turnstile). |
| **celery**`[redis]` | 5.6.3 | Tâches asynchrones (emails) + tâches planifiées (beat). |
| **sentry-sdk** | 2.64.0 | Monitoring des erreurs (Django + Celery), optionnel. |

> Extras : `[socialaccount]` (allauth) et `[redis]` (celery) tirent les
> dépendances nécessaires à Google OAuth et au broker Redis.

---

## 3. Dépendances transitives (tirées automatiquement)

Regroupées par origine/rôle. Vous n'avez pas à les installer à la main.

### Django (cœur)
| Paquet | Version | Rôle |
|---|---|---|
| `asgiref` | 3.11.1 | Couche ASGI/async de Django. |
| `sqlparse` | 0.5.3 | Formatage SQL (Django). |
| `tzdata` | 2025.2 | Base de données des fuseaux horaires. |

### Celery & broker
| Paquet | Version | Rôle |
|---|---|---|
| `kombu` | 5.6.2 | Messagerie/transports Celery. |
| `amqp` | 5.3.1 | Protocole AMQP (kombu). |
| `billiard` | 4.2.4 | Multiprocessing de Celery. |
| `vine` | 5.1.0 | Promesses (Celery). |
| `redis` | 6.4.0 | Client Redis (broker Celery + django-redis). |
| `tzlocal` | 5.4.4 | Fuseau horaire local (Celery beat). |
| `click`, `click-didyoumean`, `click-plugins`, `click-repl` | 8.4.2 / 0.3.1 / 1.1.1.2 / 0.3.0 | CLI Celery. |
| `prompt_toolkit` | 3.0.52 | Shell interactif (Celery). |
| `wcwidth` | 0.8.2 | Largeur des caractères (CLI). |

### boto3 / S3
| Paquet | Version | Rôle |
|---|---|---|
| `botocore` | 1.40.76 | Cœur du SDK AWS. |
| `s3transfer` | 0.14.0 | Transferts S3 (multipart). |
| `jmespath` | 1.1.0 | Requêtes JSON (botocore). |

### Authentification / crypto (allauth, JWT, OAuth)
| Paquet | Version | Rôle |
|---|---|---|
| `PyJWT` | 2.10.1 | Jetons JWT. |
| `oauthlib`, `requests-oauthlib` | 3.3.1 / 2.0.0 | Flux OAuth (Google). |
| `cryptography` | 45.0.2 | Primitives cryptographiques. |
| `cffi`, `pycparser` | 2.0.0 / 2.22 | Liaison C de `cryptography`. |
| `defusedxml` | 0.7.1 | Parsing XML sécurisé (allauth). |
| `dnspython` | 2.7.0 | Résolution DNS (validation d'emails). |

### HTTP (requests)
| Paquet | Version | Rôle |
|---|---|---|
| `certifi` | 2025.4.26 | Bundle de certificats CA. |
| `charset-normalizer` | 3.4.2 | Détection d'encodage. |
| `idna` | 3.10 | Noms de domaine internationalisés. |
| `urllib3` | 2.4.0 | Transport HTTP bas niveau. |

### Dates, formats & divers
| Paquet | Version | Rôle |
|---|---|---|
| `python-dateutil` | 2.9.0 | Manipulation de dates. |
| `pytz` | 2025.2 | Fuseaux horaires (héritage). |
| `six` | 1.17.0 | Compat Python 2/3 (dépendance tierce). |
| `packaging` | 25.0 | Comparaison de versions. |
| `PyYAML` | 6.0.3 | Parsing YAML. |
| `colorama` | 0.4.6 | Couleurs terminal (Windows). |
| `typing_extensions` | 4.13.2 | Annotations de type rétroportées. |
| `babel` | 2.17.0 | Présent dans l'environnement (i18n), **non importé** directement par le code — le projet utilise le `gettext` de Django. |
| `psycopg2` | 2.9.11 | Pilote PostgreSQL (variante source ; `psycopg2-binary` est la variante utilisée). |

---

## 4. Annexe — Liste verrouillée complète (`pip freeze`)

Environnement de référence (Python 3.12+, Django 6.0.6) :

```text
amqp==5.3.1
asgiref==3.11.1
babel==2.17.0
billiard==4.2.4
boto3==1.40.44
botocore==1.40.76
celery==5.6.3
certifi==2025.4.26
cffi==2.0.0
charset-normalizer==3.4.2
click==8.4.2
click-didyoumean==0.3.1
click-plugins==1.1.1.2
click-repl==0.3.0
colorama==0.4.6
cryptography==45.0.2
defusedxml==0.7.1
dj-database-url==3.1.2
Django==6.0.6
django-allauth==65.18.0
django-crispy-forms==2.6
django-formtools==2.6.1
django-jazzmin==3.0.5
django-redis==7.0.0
django-storages==1.14.6
dnspython==2.7.0
gunicorn==26.0.0
idna==3.10
jmespath==1.1.0
kombu==5.6.2
oauthlib==3.3.1
packaging==25.0
pillow==12.3.0
prompt_toolkit==3.0.52
psycopg2==2.9.11
psycopg2-binary==2.9.12
pycparser==2.22
PyJWT==2.10.1
python-dateutil==2.9.0.post0
python-decouple==3.8
pytz==2025.2
PyYAML==6.0.3
redis==6.4.0
requests==2.34.2
requests-oauthlib==2.0.0
s3transfer==0.14.0
sentry-sdk==2.64.0
six==1.17.0
sqlparse==0.5.3
typing_extensions==4.13.2
tzdata==2025.2
tzlocal==5.4.4
urllib3==2.4.0
vine==5.1.0
wcwidth==0.8.2
whitenoise==6.12.0
```

> **Note** : `babel` et `psycopg2` (source) apparaissent dans l'environnement
> sans être déclarés dans `requirements.txt`. Si vous voulez un environnement
> 100 % reproductible, envisagez de figer l'ensemble via `pip freeze` ou un
> outil de lock (uv, pip-tools).
