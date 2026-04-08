# AWS Infrastructure Health Check

Autonomous infrastructure verification. Create a TodoWrite checklist and work through each item independently. Do NOT ask questions — make reasonable decisions and document assumptions.

## Setup

Region: `us-east-1`
Cluster: `unipaith-cluster`
Service: `unipaith-backend`
Domain: `unipaith.co` / `api.unipaith.co`
S3 bucket: `unipaith-frontend`

Create a TodoWrite checklist with these 5 items, then work through each one. If any check fails, fix it before moving to the next.

## 1. RDS Connectivity from ECS

Verify the backend can reach the database.

**Credentials check:**
```bash
aws secretsmanager get-secret-value --secret-id unipaith-db-credentials --region us-east-1 --query 'SecretString' --output text | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Host: {d[\"host\"]}\nUser: {d[\"username\"]}\nDB: {d.get(\"dbname\",\"unipaith\")}')"
```

**VPC/Security group check — ECS tasks must reach RDS:**
```bash
# Get RDS security group
aws rds describe-db-instances --region us-east-1 --query "DBInstances[?DBInstanceIdentifier=='unipaith-db'].VpcSecurityGroups[*].VpcSecurityGroupId" --output text

# Get ECS task security group
aws ecs describe-services --cluster unipaith-cluster --services unipaith-backend --region us-east-1 --query "services[0].networkConfiguration.awsvpcConfiguration.securityGroups" --output text

# Verify the RDS security group allows inbound from ECS security group on port 5432
aws ec2 describe-security-groups --group-ids <RDS_SG> --region us-east-1 --query "SecurityGroups[0].IpPermissions[?FromPort==\`5432\`]" --output table
```

**DNS resolution — verify RDS endpoint resolves:**
```bash
RDS_HOST=$(aws rds describe-db-instances --region us-east-1 --query "DBInstances[?DBInstanceIdentifier=='unipaith-db'].Endpoint.Address" --output text)
echo "RDS endpoint: $RDS_HOST"
nslookup $RDS_HOST
```

**ECS task logs — check for recent DB connection errors:**
```bash
aws logs tail /ecs/unipaith-backend --since 10m --region us-east-1 --filter-pattern "connection" 2>&1 | head -20
```

Pass criteria: credentials exist, security groups allow port 5432, DNS resolves, no connection errors in logs.

## 2. ALB Health Checks & Target Groups

**Target group health:**
```bash
TG_ARN=$(aws elbv2 describe-target-groups --region us-east-1 --query "TargetGroups[?contains(TargetGroupName,'unipaith')].TargetGroupArn" --output text)
aws elbv2 describe-target-health --target-group-arn $TG_ARN --region us-east-1 --output table
```

**Health check configuration:**
```bash
aws elbv2 describe-target-groups --target-group-arns $TG_ARN --region us-east-1 --query "TargetGroups[0].{Path:HealthCheckPath,Interval:HealthCheckIntervalSeconds,Timeout:HealthCheckTimeoutSeconds,Healthy:HealthyThresholdCount,Unhealthy:UnhealthyThresholdCount}" --output table
```

**ALB listeners:**
```bash
ALB_ARN=$(aws elbv2 describe-load-balancers --region us-east-1 --query "LoadBalancers[?contains(LoadBalancerName,'unipaith')].LoadBalancerArn" --output text)
aws elbv2 describe-listeners --load-balancer-arn $ALB_ARN --region us-east-1 --query "Listeners[*].{Port:Port,Protocol:Protocol}" --output table
```

**Live health check:**
```bash
curl -sf https://api.unipaith.co/api/v1/health | python3 -m json.tool
```

Pass criteria: all targets healthy, health check endpoint returns 200, both HTTP and HTTPS listeners configured.

## 3. ECS Task Definition — Env Vars & Secrets

**Current task definition env vars:**
```bash
TASK_DEF=$(aws ecs describe-services --cluster unipaith-cluster --services unipaith-backend --region us-east-1 --query "services[0].taskDefinition" --output text)
aws ecs describe-task-definition --task-definition $TASK_DEF --region us-east-1 --query "taskDefinition.containerDefinitions[0].environment[*].{Name:name,Value:value}" --output table
```

**Secrets (from Secrets Manager / Parameter Store):**
```bash
aws ecs describe-task-definition --task-definition $TASK_DEF --region us-east-1 --query "taskDefinition.containerDefinitions[0].secrets[*].{Name:name,Source:valueFrom}" --output table
```

**Required env vars — verify ALL are present:**
- `DATABASE_URL`
- `COGNITO_USER_POOL_ID`
- `COGNITO_CLIENT_ID`
- `S3_BUCKET`
- `OPENAI_API_KEY` (may be in secrets)
- `AWS_DEFAULT_REGION`

**Running task count:**
```bash
aws ecs describe-services --cluster unipaith-cluster --services unipaith-backend --region us-east-1 --query "services[0].{Desired:desiredCount,Running:runningCount,Pending:pendingCount}" --output table
```

Pass criteria: all required env vars/secrets present, running count matches desired count, no missing or empty values.

## 4. Route53 DNS

**Verify api.unipaith.co points to ALB:**
```bash
ZONE_ID=$(aws route53 list-hosted-zones --query "HostedZones[?Name=='unipaith.co.'].Id" --output text | sed 's|/hostedzone/||')
aws route53 list-resource-record-sets --hosted-zone-id $ZONE_ID --query "ResourceRecordSets[?Name=='api.unipaith.co.']" --output table
```

**Verify unipaith.co points to CloudFront:**
```bash
aws route53 list-resource-record-sets --hosted-zone-id $ZONE_ID --query "ResourceRecordSets[?Name=='unipaith.co.']" --output table
```

**Live DNS resolution:**
```bash
nslookup api.unipaith.co
nslookup unipaith.co
```

**Verify ALB DNS matches Route53 target:**
```bash
ALB_DNS=$(aws elbv2 describe-load-balancers --region us-east-1 --query "LoadBalancers[?contains(LoadBalancerName,'unipaith')].DNSName" --output text)
echo "ALB DNS: $ALB_DNS"
```

Pass criteria: api.unipaith.co resolves to ALB, unipaith.co resolves to CloudFront, DNS records are ALIAS type.

## 5. S3 Frontend Bundle & CORS

**Check bundle freshness:**
```bash
aws s3 ls s3://unipaith-frontend/index.html
aws s3 ls s3://unipaith-frontend/ --recursive --summarize | tail -5
```

**CORS configuration:**
```bash
aws s3api get-bucket-cors --bucket unipaith-frontend --region us-east-1 --output json
```

**CloudFront distribution status:**
```bash
DIST_ID=$(aws cloudfront list-distributions --query "DistributionList.Items[?Aliases.Items[?contains(@,'unipaith.co')]].Id" --output text)
aws cloudfront get-distribution --id $DIST_ID --query "Distribution.{Status:Status,DomainName:DomainName,Enabled:DistributionConfig.Enabled}" --output table
```

**Recent invalidations:**
```bash
aws cloudfront list-invalidations --distribution-id $DIST_ID --query "InvalidationList.Items[0].{Id:Id,Status:Status,CreateTime:CreateTime}" --output table
```

**Live site check:**
```bash
curl -sf -o /dev/null -w "%{http_code}" https://unipaith.co
```

Pass criteria: index.html exists and is recent, CORS allows unipaith.co origins, CloudFront enabled and deployed, site returns 200.

## Final Report

Print a summary table:

| Check                        | Status | Details          |
|------------------------------|--------|------------------|
| 1. RDS Connectivity          | ...    | ...              |
| 2. ALB Health / Targets      | ...    | ...              |
| 3. ECS Env Vars / Secrets    | ...    | ...              |
| 4. Route53 DNS               | ...    | ...              |
| 5. S3 Bundle / CORS          | ...    | ...              |

If all pass: **AWS INFRASTRUCTURE HEALTHY**

If any failed and was fixed: list what was fixed and what command confirmed the fix.

If any failed and could not be fixed: list the blocker, what was tried, and assumptions made.
