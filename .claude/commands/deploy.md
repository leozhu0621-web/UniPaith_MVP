# Deploy to Production

Deploy UniPaith to AWS. Accepts an optional argument: `backend`, `frontend`, or `all` (default: `all`).

## Pre-Deploy Checks

Run these before ANY deployment. Do NOT skip.

1. **Full test suite must pass:**
```bash
make test-backend && make test-frontend
```

2. **Frontend must compile with zero TypeScript errors:**
```bash
cd frontend && npx tsc -b --noEmit
```

3. **Backend lint must be clean:**
```bash
cd unipaith-backend && .venv/bin/ruff check src/ tests/
```

If any pre-deploy check fails, STOP and fix it before deploying.

## Deploy Backend

1. Build and push Docker image to ECR:
```bash
./scripts/deploy.sh backend
```

2. **CRITICAL — Verify env vars survived the deployment.** ECS task definitions can overwrite env vars on redeploy. Check:
```bash
aws ecs describe-task-definition --task-definition unipaith-backend --region us-east-1 --query 'taskDefinition.containerDefinitions[0].environment' --output table
```
Verify these are present: `DATABASE_URL`, `COGNITO_USER_POOL_ID`, `COGNITO_CLIENT_ID`, `S3_BUCKET`, `OPENAI_API_KEY`.

Also check secrets:
```bash
aws ecs describe-task-definition --task-definition unipaith-backend --region us-east-1 --query 'taskDefinition.containerDefinitions[0].secrets' --output table
```

3. Wait for ECS service to stabilize:
```bash
aws ecs wait services-stable --cluster unipaith-cluster --services unipaith-backend --region us-east-1
```

## Deploy Frontend

1. Build and deploy to S3 + invalidate CloudFront:
```bash
./scripts/deploy.sh frontend
```

2. **Verify the S3 bundle is fresh** (not stale from a previous deploy):
```bash
aws s3 ls s3://unipaith-frontend/index.html
```
Confirm the timestamp is from the current deployment.

3. **Verify CloudFront invalidation completed:**
```bash
DIST_ID=$(aws cloudfront list-distributions --query "DistributionList.Items[?Aliases.Items[?contains(@,'unipaith.co')]].Id" --output text)
aws cloudfront list-invalidations --distribution-id $DIST_ID --query 'InvalidationList.Items[0]' --output table
```

## Post-Deploy Verification

Run ALL of these after every deployment. Do NOT skip.

1. **API health check:**
```bash
curl -sf https://api.unipaith.co/api/v1/health | python3 -m json.tool
```

2. **RDS connectivity from ECS** — check ECS task logs for DB connection errors:
```bash
aws logs tail /ecs/unipaith-backend --since 5m --region us-east-1 | head -30
```

3. **Verify login works** — test both accounts:
   - Student: `student@unipaith.co` (do NOT change this account)
   - Institution: `institution@unipaith.co` / `Unipaith2026` (do NOT change this account)

4. **Verify site loads:**
```bash
curl -sf -o /dev/null -w "%{http_code}" https://unipaith.co
```
Must return 200.

## Known Gotchas

These are recurring issues from past deployments. Check for them proactively:

- **Stale S3 bundles:** Always invalidate CloudFront after frontend deploy. The deploy script does this, but verify it completed.
- **ECS task def env var overwrite:** A new task definition revision can drop env vars. Always verify after backend deploy (step 2 above).
- **DB password mismatch:** If RDS password was rotated, update AWS Secrets Manager AND the ECS task definition. Check logs for auth errors.
- **VPC/Security group:** ECS tasks must be in the same VPC as RDS. If a new task fails to connect to the DB, check security group rules:
```bash
aws ec2 describe-security-groups --filters "Name=group-name,Values=*unipaith*" --query 'SecurityGroups[*].[GroupName,GroupId]' --output table --region us-east-1
```
- **DNS pointing to old ALB:** After infra changes, verify Route53 points to the current ALB:
```bash
aws route53 list-resource-record-sets --hosted-zone-id $(aws route53 list-hosted-zones --query "HostedZones[?Name=='unipaith.co.'].Id" --output text | sed 's|/hostedzone/||') --query "ResourceRecordSets[?Name=='api.unipaith.co.']" --output table
```

## Report

Print a post-deploy summary:

| Check                  | Status |
|------------------------|--------|
| Pre-deploy tests       | ...    |
| Backend deploy         | ...    |
| Frontend deploy        | ...    |
| API health             | ...    |
| ECS logs clean         | ...    |
| Site loads (200)       | ...    |
| Login verified         | ...    |

If all pass: **DEPLOYMENT SUCCESSFUL**
If any fail: list the issue and fix it before moving on.
