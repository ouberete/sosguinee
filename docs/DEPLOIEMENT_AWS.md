# Déploiement SOS Guinée sur AWS (EKS + S3)

> Guide pas-à-pas pour déployer la plateforme sur **Amazon EKS** (Kubernetes
> managé) avec les médias sur **Amazon S3** (bucket public + bucket privé).
> Complète le [guide de prise en main](guide_prise_en_main.md) (section 6) et la
> [documentation technique](documentation_technique.md).

Les manifestes Kubernetes de base sont dans [`k8s/`](../k8s/). Ce guide ne
décrit que les spécificités AWS ; la logique applicative est identique à OVH
(voir [`DEPLOIEMENT_OVH.md`](DEPLOIEMENT_OVH.md)).

---

## 0. Prérequis

- Un compte AWS avec droits d'admin sur EKS, ECR, S3, IAM (et RDS si base managée).
- CLI installées : `aws`, `eksctl`, `kubectl`, `kustomize`, `docker`, `helm`.
- Un nom de domaine (ex: `sosguinee.org`) dont vous gérez le DNS.
- `aws configure` effectué (région ex. `eu-west-3` = Paris).

```bash
export AWS_REGION=eu-west-3
export CLUSTER=sosguinee
export ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
```

---

## 1. Registre d'images (ECR)

```bash
aws ecr create-repository --repository-name sosguinee --region $AWS_REGION

# Connexion Docker à ECR
aws ecr get-login-password --region $AWS_REGION \
  | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Build + push (tag versionné, jamais latest)
export IMAGE=$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/sosguinee:v1.0.0
docker build -t $IMAGE .
docker push $IMAGE
```

---

## 2. Cluster EKS

```bash
eksctl create cluster \
  --name $CLUSTER --region $AWS_REGION \
  --nodegroup-name std --node-type t3.medium --nodes 2 --nodes-min 2 --nodes-max 4 \
  --managed
# kubectl est configuré automatiquement par eksctl
kubectl get nodes
```

### Ingress + TLS

```bash
# ingress-nginx (crée un Network Load Balancer AWS)
helm upgrade --install ingress-nginx ingress-nginx \
  --repo https://kubernetes.github.io/ingress-nginx --namespace ingress-nginx --create-namespace

# cert-manager (Let's Encrypt)
helm upgrade --install cert-manager cert-manager \
  --repo https://charts.jetstack.io --namespace cert-manager --create-namespace \
  --set installCRDs=true
```

Créez un `ClusterIssuer` `letsencrypt-prod` :

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

## 3. Stockage objet (S3) — 2 buckets

```bash
export BUCKET_PUBLIC=sosguinee-media
export BUCKET_PRIVATE=sosguinee-private

aws s3api create-bucket --bucket $BUCKET_PUBLIC  --region $AWS_REGION \
  --create-bucket-configuration LocationConstraint=$AWS_REGION
aws s3api create-bucket --bucket $BUCKET_PRIVATE --region $AWS_REGION \
  --create-bucket-configuration LocationConstraint=$AWS_REGION
```

### 3.1 Bucket PUBLIC : lecture publique

```bash
# Autoriser les policies publiques (désactiver le blocage global)
aws s3api put-public-access-block --bucket $BUCKET_PUBLIC \
  --public-access-block-configuration \
  BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false

# Policy : lecture seule publique des objets
aws s3api put-bucket-policy --bucket $BUCKET_PUBLIC --policy "{
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

### 3.2 Bucket PRIVÉ : rester totalement fermé

```bash
# On garde le blocage public par défaut (ne rien changer) : aucun accès anonyme.
aws s3api put-public-access-block --bucket $BUCKET_PRIVATE \
  --public-access-block-configuration \
  BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
```

> Les pièces d'identité vivent dans le bucket privé : elles ne sont jamais
> accessibles directement, seulement via la vue Django `protected_user_document`.

### 3.3 Utilisateur IAM applicatif (clés d'accès)

Créez un utilisateur IAM programmatique avec une policy limitée aux deux buckets :

```bash
aws iam create-user --user-name sosguinee-app
aws iam put-user-policy --user-name sosguinee-app --policy-name s3-access --policy-document "{
  \"Version\": \"2012-10-17\",
  \"Statement\": [{
    \"Effect\": \"Allow\",
    \"Action\": [\"s3:GetObject\",\"s3:PutObject\",\"s3:DeleteObject\",\"s3:ListBucket\"],
    \"Resource\": [
      \"arn:aws:s3:::$BUCKET_PUBLIC\",  \"arn:aws:s3:::$BUCKET_PUBLIC/*\",
      \"arn:aws:s3:::$BUCKET_PRIVATE\", \"arn:aws:s3:::$BUCKET_PRIVATE/*\"
    ]
  }]
}"
aws iam create-access-key --user-name sosguinee-app
# -> notez AccessKeyId et SecretAccessKey pour le Secret Kubernetes
```

> **Mieux (optionnel)** : utiliser **IRSA** (IAM Roles for Service Accounts)
> pour éviter des clés statiques. Dans ce cas, laissez `AWS_ACCESS_KEY_ID` /
> `AWS_SECRET_ACCESS_KEY` vides et attachez le rôle au ServiceAccount du pod web.

---

## 4. Base de données (recommandé : RDS PostgreSQL)

Créez une instance **RDS PostgreSQL** (via console ou CLI), puis pointez
l'application dessus avec `DATABASE_URL` (prioritaire sur les `POSTGRES_*`).
Dans ce cas, **supprimez `postgres.yaml`** de `k8s/kustomization.yaml`.

```
DATABASE_URL=postgres://<user>:<pass>@<endpoint-rds>:5432/sosguinee
```

Sinon, gardez le PostgreSQL in-cluster fourni (`postgres.yaml`) — acceptable
pour démarrer, mais prévoyez sauvegardes et volume adéquat.

---

## 5. Configuration K8s (ConfigMap + Secret)

### 5.1 ConfigMap — valeurs AWS

Éditez `k8s/configmap.yaml` :

```yaml
ALLOWED_HOSTS: "sosguinee.org"
CSRF_TRUSTED_ORIGINS: "https://sosguinee.org"
SITE_URL: "https://sosguinee.org"
DJOMY_BASE_URL: "https://api.djomy.africa/v1"

USE_S3: "True"
AWS_STORAGE_BUCKET_NAME: "sosguinee-media"
AWS_PRIVATE_STORAGE_BUCKET_NAME: "sosguinee-private"
AWS_S3_REGION_NAME: "eu-west-3"
AWS_S3_ENDPOINT_URL: ""          # VIDE pour AWS S3
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
  --from-literal=AWS_ACCESS_KEY_ID='<AccessKeyId IAM>' \
  --from-literal=AWS_SECRET_ACCESS_KEY='<SecretAccessKey IAM>' \
  --from-literal=TURNSTILE_SITE_KEY='<...>' \
  --from-literal=TURNSTILE_SECRET_KEY='<...>' \
  --from-literal=SENTRY_DSN=''
```

> Le domaine de l'ingress (`k8s/ingress.yaml`) et le header `Host` des probes
> (`k8s/web.yaml`) doivent aussi contenir `sosguinee.org`.

---

## 6. Déploiement

```bash
# Pointer l'image ECR
cd k8s && kustomize edit set image REGISTRY/sosguinee=$IMAGE && cd ..

kubectl apply -k k8s/

# Migrations (à relancer à CHAQUE déploiement)
kubectl -n sosguinee delete job sosguinee-migrate --ignore-not-found
kubectl -n sosguinee apply -f k8s/migrate-job.yaml
kubectl -n sosguinee wait --for=condition=complete job/sosguinee-migrate --timeout=300s

kubectl -n sosguinee get pods
kubectl -n sosguinee exec -it deploy/sosguinee-web -- python manage.py createsuperuser
```

### DNS

Récupérez le hostname du Load Balancer et créez un enregistrement DNS
`CNAME` (ou `A` alias Route 53) vers celui-ci :

```bash
kubectl -n ingress-nginx get svc ingress-nginx-controller \
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'
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

1. `curl -H "Host: sosguinee.org" http://<LB>/healthz/` → `{"status": "ok"}`.
2. Uploader une **image d'alerte** → elle doit s'afficher (servie depuis le
   bucket public, URL `https://sosguinee-media.s3.eu-west-3.amazonaws.com/...`).
3. Uploader une **pièce d'identité** → visible **seulement** par le
   propriétaire/staff via `/media/user_images/...`, et **inaccessible** en
   direct sur S3 (403).
4. Faire un **don test** Djomy → paiement confirmé + email reçu.
5. Vérifier les logs : `kubectl -n sosguinee logs -f deploy/sosguinee-web`.

---

## 9. Mises à jour

```bash
docker build -t $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/sosguinee:v1.0.1 .
docker push  $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/sosguinee:v1.0.1
cd k8s && kustomize edit set image REGISTRY/sosguinee=$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/sosguinee:v1.0.1 && cd ..
kubectl apply -k k8s/            # rolling update
# relancer le job de migration (cf. §6)
```

Rollback : `kubectl -n sosguinee rollout undo deploy/sosguinee-web`.
