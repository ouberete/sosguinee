# Déploiement Kubernetes — Ensemble 224

Manifestes de production. Le guide détaillé (prérequis, construction de
l'image, pas-à-pas complet, opérations courantes) est dans
[`docs/guide_prise_en_main.md`](../docs/guide_prise_en_main.md).

## Contenu

| Fichier | Rôle |
|---|---|
| `namespace.yaml` | Namespace `ensemble224` |
| `configmap.yaml` | Configuration non sensible (hôtes, DB, Redis, email…) |
| `secret.example.yaml` | **Modèle** de secrets — ne jamais committer le vrai |
| `postgres.yaml` | PostgreSQL (StatefulSet + PVC) — ou base managée |
| `redis.yaml` | Redis (broker Celery + cache/rate limiting) |
| `web.yaml` | Django/gunicorn (2 répliques, probes `/healthz/`) |
| `celery-worker.yaml` | Worker emails asynchrones |
| `celery-beat.yaml` | Tâches planifiées (1 réplique obligatoire) |
| `migrate-job.yaml` | Job de migration à lancer à chaque déploiement |
| `ingress.yaml` | HTTPS via ingress-nginx + cert-manager |
| `hpa.yaml` | Autoscaling du web (2→5 répliques) |
| `kustomization.yaml` | Application groupée `kubectl apply -k` |

## Démarrage rapide

```bash
# 1. Adapter les placeholders
#    - REGISTRY/ensemble224:latest  -> votre image (web, worker, beat, migrate)
#    - ensemble224.example.com      -> votre domaine (configmap, web, ingress)

# 2. Namespace + secrets (JAMAIS dans git)
kubectl apply -f k8s/namespace.yaml
kubectl -n ensemble224 create secret generic ensemble224-secrets \
  --from-literal=SECRET_KEY='...' \
  --from-literal=POSTGRES_PASSWORD='...' \
  # ... voir secret.example.yaml pour la liste complète

# 3. Tout déployer
kubectl apply -k k8s/

# 4. Migrations (à refaire à chaque déploiement)
kubectl -n ensemble224 delete job ensemble224-migrate --ignore-not-found
kubectl -n ensemble224 apply -f k8s/migrate-job.yaml
kubectl -n ensemble224 wait --for=condition=complete job/ensemble224-migrate --timeout=300s

# 5. Vérifier
kubectl -n ensemble224 get pods
kubectl -n ensemble224 logs deploy/ensemble224-web
```

## Mise à jour applicative

```bash
docker build -t REGISTRY/ensemble224:v1.x.y . && docker push REGISTRY/ensemble224:v1.x.y
cd k8s && kustomize edit set image REGISTRY/ensemble224=REGISTRY/ensemble224:v1.x.y
kubectl apply -k k8s/            # rolling update sans coupure
# puis relancer le job de migration (étape 4 ci-dessus)
```

## Points d'attention

- **Secrets** : le fichier `secret.example.yaml` est un modèle. En GitOps,
  utilisez SealedSecrets ou External Secrets Operator.
- **Médias (S3/Object Storage)** : les fichiers uploadés sont stockés sur un
  service objet S3-compatible (bucket public + bucket privé), plus de PVC.
  Guides dédiés : [`docs/DEPLOIEMENT_AWS.md`](../docs/DEPLOIEMENT_AWS.md) et
  [`docs/DEPLOIEMENT_OVH.md`](../docs/DEPLOIEMENT_OVH.md).
- **PostgreSQL** : une base managée est recommandée en production réelle
  (sauvegardes/HA). Le StatefulSet fourni convient pour démarrer.
- **celery-beat** : ne jamais dépasser 1 réplique (tâches en double sinon).
- **Webhook Djomy** : déclarez `https://<domaine>/djomy/webhook/` chez Djomy
  une fois l'ingress actif.
