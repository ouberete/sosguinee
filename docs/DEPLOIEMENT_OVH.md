# Déploiement SOS Guinée sur OVHcloud (Managed Kubernetes + Object Storage)

> Guide pas-à-pas pour déployer la plateforme sur **OVH Managed Kubernetes
> (MKS)** avec les médias sur **OVH Object Storage S3-compatible** (bucket
> public + bucket privé). Complète le [guide de prise en main](guide_prise_en_main.md)
> (section 6) et la [documentation technique](documentation_technique.md).

Les manifestes Kubernetes de base sont dans [`k8s/`](../k8s/). Ce guide ne
décrit que les spécificités OVH ; la logique applicative est identique à AWS
(voir [`DEPLOIEMENT_AWS.md`](DEPLOIEMENT_AWS.md)).

---

## 0. Prérequis

- Un projet **Public Cloud** OVHcloud (avec quota Kubernetes + Object Storage).
- CLI installées : `kubectl`, `kustomize`, `docker`, `helm`, et
  `aws` (client S3 générique) OU `s3cmd`.
- Un nom de domaine (ex: `sosguinee.org`) dont vous gérez le DNS.
- Région OVH choisie (ex: `GRA` = Gravelines). Endpoint S3 associé :
  `https://s3.gra.io.cloud.ovh.net`.

```bash
export OVH_REGION=gra
export S3_ENDPOINT=https://s3.$OVH_REGION.io.cloud.ovh.net
```

---

## 1. Registre d'images

Créez un **Managed Private Registry** OVH (basé sur Harbor) depuis le manager
Public Cloud, puis :

```bash
docker login <votre-registry>.<region>.container-registry.ovh.net
export IMAGE=<votre-registry>.<region>.container-registry.ovh.net/sosguinee/app:v1.0.0
docker build -t $IMAGE .
docker push $IMAGE
```

> Alternative : Docker Hub ou GHCR si vous ne voulez pas du registre OVH.

---

## 2. Cluster Managed Kubernetes (MKS)

Créez le cluster depuis le manager OVH (ou l'API/Terraform), ajoutez un
node pool (ex: 2× `b2-7`), puis téléchargez le kubeconfig :

```bash
export KUBECONFIG=~/.kube/ovh-sosguinee.yml   # fichier fourni par OVH
kubectl get nodes
```

### Ingress + TLS

```bash
# ingress-nginx (OVH provisionne un Load Balancer public)
helm upgrade --install ingress-nginx ingress-nginx \
  --repo https://kubernetes.github.io/ingress-nginx --namespace ingress-nginx --create-namespace

# cert-manager (Let's Encrypt)
helm upgrade --install cert-manager cert-manager \
  --repo https://charts.jetstack.io --namespace cert-manager --create-namespace \
  --set installCRDs=true
```

`ClusterIssuer` `letsencrypt-prod` :

```bash
kubectl apply -f - <<'EOF'
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@sosguinee.org
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
      - http01:
          ingress:
            ingressClassName: nginx
EOF
```

---

## 3. Object Storage (S3-compatible) — 2 buckets

OVH propose l'**Object Storage S3** (« High Performance » ou « Standard »).
Depuis le manager : Public Cloud → Object Storage → créez un **utilisateur S3**
et récupérez sa paire de clés (`access_key` / `secret_key`).

Configurez le client `aws` pour pointer l'endpoint OVH :

```bash
aws configure set aws_access_key_id     <access_key_ovh>
aws configure set aws_secret_access_key <secret_key_ovh>
aws configure set region $OVH_REGION

export BUCKET_PUBLIC=sosguinee-media
export BUCKET_PRIVATE=sosguinee-private
export S3="aws --endpoint-url $S3_ENDPOINT s3"
export S3API="aws --endpoint-url $S3_ENDPOINT s3api"

$S3 mb s3://$BUCKET_PUBLIC
$S3 mb s3://$BUCKET_PRIVATE
```

### 3.1 Bucket PUBLIC : lecture publique

```bash
$S3API put-bucket-policy --bucket $BUCKET_PUBLIC --policy "{
  \"Version\": \"2012-10-17\",
  \"Statement\": [{
    \"Sid\": \"PublicRead\",
    \"Effect\": \"Allow\",
    \"Principal\": \"*\",
    \"Action\": \"s3:GetObject\",
    \"Resource\": \"arn:aws:s3:::$BUCKET_PUBLIC/*\"
  }]
}"
```

### 3.2 Bucket PRIVÉ : rester fermé

Ne mettez **aucune** policy publique sur `$BUCKET_PRIVATE` : par défaut, seuls
les détenteurs des clés S3 y accèdent. Les pièces d'identité y sont stockées et
ne sortent que par la vue Django `protected_user_document`.

> Astuce vérification : `aws --endpoint-url $S3_ENDPOINT s3api get-bucket-policy
> --bucket $BUCKET_PRIVATE` doit renvoyer une erreur (pas de policy publique).

---

## 4. Base de données (recommandé : OVH Managed Databases for PostgreSQL)

Créez une instance **Managed Databases PostgreSQL** depuis le manager OVH,
autorisez l'IP sortante du cluster, puis utilisez `DATABASE_URL` :

```
DATABASE_URL=postgres://<user>:<pass>@<host-ovh>:<port>/sosguinee?sslmode=require
```

Dans ce cas, **retirez `postgres.yaml`** de `k8s/kustomization.yaml`.
Sinon, gardez le PostgreSQL in-cluster (`postgres.yaml`) pour démarrer.

---

## 5. Configuration K8s (ConfigMap + Secret)

### 5.1 ConfigMap — valeurs OVH

Éditez `k8s/configmap.yaml` :

```yaml
ALLOWED_HOSTS: "sosguinee.org"
CSRF_TRUSTED_ORIGINS: "https://sosguinee.org"
SITE_URL: "https://sosguinee.org"
DJOMY_BASE_URL: "https://api.djomy.africa/v1"

USE_S3: "True"
AWS_STORAGE_BUCKET_NAME: "sosguinee-media"
AWS_PRIVATE_STORAGE_BUCKET_NAME: "sosguinee-private"
AWS_S3_REGION_NAME: "gra"                              # région OVH
AWS_S3_ENDPOINT_URL: "https://s3.gra.io.cloud.ovh.net"  # endpoint OVH (≠ AWS)
```

### 5.2 Secret

```bash
kubectl apply -f k8s/namespace.yaml
kubectl -n sosguinee create secret generic sosguinee-secrets \
  --from-literal=SECRET_KEY="$(python -c 'import secrets;print(secrets.token_urlsafe(64))')" \
  --from-literal=POSTGRES_PASSWORD='<si postgres in-cluster>' \
  --from-literal=EMAIL_HOST_USER='notifications@sosguinee.org' \
  --from-literal=EMAIL_HOST_PASSWORD='<mot de passe application>' \
  --from-literal=CONTACT_NOTIFY_EMAIL='equipe@sosguinee.org' \
  --from-literal=DJOMY_CLIENT_ID='<...>' \
  --from-literal=DJOMY_CLIENT_SECRET='<...>' \
  --from-literal=DJOMY_WEBHOOK_SECRET='<= DJOMY_CLIENT_SECRET sauf indication contraire de Djomy>' \
  --from-literal=AWS_ACCESS_KEY_ID='<access_key OVH S3>' \
  --from-literal=AWS_SECRET_ACCESS_KEY='<secret_key OVH S3>' \
  --from-literal=TURNSTILE_SITE_KEY='<...>' \
  --from-literal=TURNSTILE_SECRET_KEY='<...>' \
  --from-literal=SENTRY_DSN=''
```

> Le domaine de l'ingress (`k8s/ingress.yaml`) et le header `Host` des probes
> (`k8s/web.yaml`) doivent aussi contenir `sosguinee.org`.

---

## 6. Déploiement

```bash
# Pointer l'image du registre OVH
cd k8s && kustomize edit set image REGISTRY/sosguinee=$IMAGE && cd ..

# Si registre privé OVH, créez un secret de pull et référencez-le
# (imagePullSecrets) dans web.yaml / celery-*.yaml si nécessaire :
# kubectl -n sosguinee create secret docker-registry ovh-registry \
#   --docker-server=<registry>.container-registry.ovh.net \
#   --docker-username=<user> --docker-password=<pass>

kubectl apply -k k8s/

# Migrations (à relancer à CHAQUE déploiement)
kubectl -n sosguinee delete job sosguinee-migrate --ignore-not-found
kubectl -n sosguinee apply -f k8s/migrate-job.yaml
kubectl -n sosguinee wait --for=condition=complete job/sosguinee-migrate --timeout=300s

kubectl -n sosguinee get pods
kubectl -n sosguinee exec -it deploy/sosguinee-web -- python manage.py createsuperuser
```

### DNS

Récupérez l'IP publique du Load Balancer OVH et créez un enregistrement `A` :

```bash
kubectl -n ingress-nginx get svc ingress-nginx-controller \
  -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
```

Le certificat TLS est émis automatiquement par cert-manager sous 1–2 min.

---

## 7. Webhook Djomy

Dans le dashboard Djomy, déclarez l'URL de webhook :

```
https://sosguinee.org/djomy/webhook/
```

(URL stable, hors préfixe i18n, HTTPS.)

---

## 8. Validation post-déploiement

1. `curl -H "Host: sosguinee.org" http://<IP-LB>/healthz/` → `{"status": "ok"}`.
2. Uploader une **image d'alerte** → elle doit s'afficher (servie depuis le
   bucket public, URL `https://sosguinee-media.s3.gra.io.cloud.ovh.net/...`).
3. Uploader une **pièce d'identité** → visible **seulement** par le
   propriétaire/staff via `/media/user_images/...`, et **inaccessible** en
   direct sur l'endpoint S3 OVH.
4. Faire un **don test** Djomy → paiement confirmé + email reçu.
5. Vérifier les logs : `kubectl -n sosguinee logs -f deploy/sosguinee-web`.

---

## 9. Mises à jour

```bash
docker build -t <registry>.container-registry.ovh.net/sosguinee/app:v1.0.1 .
docker push  <registry>.container-registry.ovh.net/sosguinee/app:v1.0.1
cd k8s && kustomize edit set image REGISTRY/sosguinee=<registry>.container-registry.ovh.net/sosguinee/app:v1.0.1 && cd ..
kubectl apply -k k8s/            # rolling update
# relancer le job de migration (cf. §6)
```

Rollback : `kubectl -n sosguinee rollout undo deploy/sosguinee-web`.

---

## 10. Différences clés AWS ↔ OVH (mémo)

| Sujet | AWS | OVH |
|---|---|---|
| Kubernetes | EKS | Managed Kubernetes (MKS) |
| Registre | ECR | Managed Private Registry (Harbor) |
| Objet | S3 | Object Storage S3-compatible |
| `AWS_S3_ENDPOINT_URL` | **vide** | `https://s3.<region>.io.cloud.ovh.net` |
| `AWS_S3_REGION_NAME` | ex. `eu-west-3` | ex. `gra` |
| Base managée | RDS | Managed Databases PostgreSQL |
| Load Balancer | NLB (hostname) | LB OVH (IP) |
| Clés S3 | utilisateur IAM (ou IRSA) | utilisateur S3 Object Storage |
