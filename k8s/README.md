# Déploiement Kubernetes — SOS Guinée

Manifestes de production. Le guide détaillé (prérequis, construction de
l'image, pas-à-pas complet, opérations courantes) est dans
[`docs/guide_prise_en_main.md`](../docs/guide_prise_en_main.md).

## Contenu

| Fichier | Rôle |
|---|---|
| `namespace.yaml` | Namespace `sosguinee` |
| `configmap.yaml` | Configuration non sensible (hôtes, DB, Redis, email…) |
| `secret.example.yaml` | **Modèle** de secrets — ne jamais committer le vrai |
| `postgres.yaml` | PostgreSQL (StatefulSet + PVC) — ou base managée |
| `redis.yaml` | Redis (broker Celery + cache/rate limiting) |
| `media-pvc.yaml` | Volume partagé des fichiers uploadés (RWX) |
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
#    - REGISTRY/sosguinee:latest  -> votre image (web, worker, beat, migrate)
#    - sosguinee.example.com      -> votre domaine (configmap, web, ingress)

# 2. Namespace + secrets (JAMAIS dans git)
kubectl apply -f k8s/namespace.yaml
kubectl -n sosguinee create secret generic sosguinee-secrets \
  --from-literal=SECRET_KEY='...' \
  --from-literal=POSTGRES_PASSWORD='...' \
  # ... voir secret.example.yaml pour la liste complète

# 3. Tout déployer
kubectl apply -k k8s/

# 4. Migrations (à refaire à chaque déploiement)
kubectl -n sosguinee delete job sosguinee-migrate --ignore-not-found
kubectl -n sosguinee apply -f k8s/migrate-job.yaml
kubectl -n sosguinee wait --for=condition=complete job/sosguinee-migrate --timeout=300s

# 5. Vérifier
kubectl -n sosguinee get pods
kubectl -n sosguinee logs deploy/sosguinee-web
```

## Mise à jour applicative

```bash
docker build -t REGISTRY/sosguinee:v1.x.y . && docker push REGISTRY/sosguinee:v1.x.y
cd k8s && kustomize edit set image REGISTRY/sosguinee=REGISTRY/sosguinee:v1.x.y
kubectl apply -k k8s/            # rolling update sans coupure
# puis relancer le job de migration (étape 4 ci-dessus)
```

## Points d'attention

- **Secrets** : le fichier `secret.example.yaml` est un modèle. En GitOps,
  utilisez SealedSecrets ou External Secrets Operator.
- **Media (RWX)** : plusieurs répliques web exigent un StorageClass
  ReadWriteMany. À défaut, `replicas: 1` sur le web, ou stockage objet S3.
- **PostgreSQL** : une base managée est recommandée en production réelle
  (sauvegardes/HA). Le StatefulSet fourni convient pour démarrer.
- **celery-beat** : ne jamais dépasser 1 réplique (tâches en double sinon).
- **Webhook Djomy** : déclarez `https://<domaine>/djomy/webhook/` chez Djomy
  une fois l'ingress actif.
