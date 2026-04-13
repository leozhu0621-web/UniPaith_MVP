#!/bin/bash
set -euo pipefail

# UniPaith Deployment Script
# Usage: ./scripts/deploy.sh [backend|frontend|infra|all]

REGION="us-east-1"
PROJECT="unipaith"
ECR_REPO="${PROJECT}-backend"
ECS_CLUSTER="${PROJECT}-cluster"
ECS_SERVICE="${PROJECT}-backend"
S3_FRONTEND="${PROJECT}-frontend"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[DEPLOY]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

check_prerequisites() {
    command -v aws >/dev/null 2>&1 || error "AWS CLI not installed. Run: brew install awscli"
    command -v docker >/dev/null 2>&1 || error "Docker not installed."
    command -v terraform >/dev/null 2>&1 || error "Terraform not installed. Run: brew install terraform"
    aws sts get-caller-identity >/dev/null 2>&1 || error "AWS credentials not configured. Run: aws configure"
    log "Prerequisites OK"
}

deploy_infra() {
    log "Deploying infrastructure with Terraform..."
    cd infra
    terraform init
    terraform plan -out=tfplan
    echo ""
    read -p "Apply this plan? (y/N): " confirm
    if [[ "$confirm" == "y" || "$confirm" == "Y" ]]; then
        terraform apply tfplan
        log "Infrastructure deployed!"
    else
        warn "Skipped infrastructure deployment."
    fi
    cd ..
}

deploy_backend() {
    log "Building and deploying backend..."

    # Get ECR login
    AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
    ECR_URL="${AWS_ACCOUNT}.dkr.ecr.${REGION}.amazonaws.com"
    aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_URL

    # Build and push
    cd unipaith-backend
    IMAGE_TAG=$(git rev-parse --short HEAD 2>/dev/null || echo "latest")
    log "Building image: ${ECR_URL}/${ECR_REPO}:${IMAGE_TAG}"
    docker build --platform linux/amd64 -t ${ECR_URL}/${ECR_REPO}:${IMAGE_TAG} .
    docker tag ${ECR_URL}/${ECR_REPO}:${IMAGE_TAG} ${ECR_URL}/${ECR_REPO}:latest
    docker push ${ECR_URL}/${ECR_REPO}:${IMAGE_TAG}
    docker push ${ECR_URL}/${ECR_REPO}:latest
    cd ..

    # Force new ECS deployment
    log "Triggering ECS deployment..."
    aws ecs update-service --cluster $ECS_CLUSTER --service $ECS_SERVICE --force-new-deployment --region $REGION >/dev/null
    log "Backend deployment triggered! ECS will roll out new tasks."
    log "Watch status: aws ecs wait services-stable --cluster $ECS_CLUSTER --services $ECS_SERVICE"
}

deploy_frontend() {
    log "Building and deploying frontend..."
    cd frontend
    npm ci
    VITE_API_URL=https://api.unipaith.co/api/v1 npm run build
    log "Uploading to S3..."
    aws s3 sync dist/ s3://${S3_FRONTEND}/ --delete \
        --cache-control "max-age=31536000,public,immutable" \
        --exclude "index.html" --exclude "*.json"
    aws s3 cp dist/index.html s3://${S3_FRONTEND}/index.html \
        --cache-control "no-cache,no-store,must-revalidate"
    cd ..

    # Invalidate CloudFront
    DIST_ID=$(aws cloudfront list-distributions --query "DistributionList.Items[?Aliases.Items[?contains(@,'unipaith.co')]].Id" --output text)
    if [ -n "$DIST_ID" ]; then
        aws cloudfront create-invalidation --distribution-id $DIST_ID --paths "/*" >/dev/null
        log "CloudFront cache invalidated."
    fi
    log "Frontend deployed!"
}

# --- Main ---
check_prerequisites

case "${1:-all}" in
    infra)
        deploy_infra
        ;;
    backend)
        deploy_backend
        ;;
    frontend)
        deploy_frontend
        ;;
    all)
        deploy_infra
        deploy_backend
        deploy_frontend
        log "=== Full deployment complete! ==="
        log "Site: https://app.unipaith.co"
        log "API:  https://api.unipaith.co/api/v1/health"
        ;;
    *)
        echo "Usage: $0 [backend|frontend|infra|all]"
        exit 1
        ;;
esac
