# --- ECS Cluster ---
resource "aws_ecs_cluster" "main" {
  name = "${var.project}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

# --- CloudWatch Log Group ---
resource "aws_cloudwatch_log_group" "backend" {
  name              = "/ecs/${var.project}-backend"
  retention_in_days = 30
}

# --- ECS Task Execution Role ---
resource "aws_iam_role" "ecs_execution" {
  name = "${var.project}-ecs-execution"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_execution" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy" "ecs_execution_secrets" {
  name = "secrets-access"
  role = aws_iam_role.ecs_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "secretsmanager:GetSecretValue",
      ]
      Resource = [
        aws_secretsmanager_secret.db_password.arn,
        aws_secretsmanager_secret.app_secret.arn,
        aws_secretsmanager_secret.openai_api_key.arn,
        aws_secretsmanager_secret.anthropic_api_key.arn,
        aws_secretsmanager_secret.voyage_api_key.arn,
      ]
    }]
  })
}

# --- ECS Task Role (app permissions) ---
resource "aws_iam_role" "ecs_task" {
  name = "${var.project}-ecs-task"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "ecs_task_permissions" {
  name = "app-permissions"
  role = aws_iam_role.ecs_task.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket",
        ]
        Resource = [
          "arn:aws:s3:::${var.project}-documents",
          "arn:aws:s3:::${var.project}-documents/*",
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "ses:SendEmail",
          "ses:SendRawEmail",
        ]
        Resource = ["*"]
      },
      {
        Effect = "Allow"
        Action = [
          "cognito-idp:AdminGetUser",
          "cognito-idp:ListUsers",
          # Signup flow — AuthService.signup() calls sign_up() (which is
          # unauthenticated and unaffected) then admin_confirm_sign_up()
          # so the user can log in immediately without verifying email.
          # Without this permission, every signup returns AccessDenied.
          "cognito-idp:AdminConfirmSignUp",
        ]
        Resource = ["*"]
      },
    ]
  })
}

# --- Security Group for ECS Tasks ---
resource "aws_security_group" "ecs_tasks" {
  name_prefix = "${var.project}-ecs-"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
    description     = "HTTP from ALB"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.project}-ecs-sg" }

  lifecycle {
    create_before_destroy = true
  }
}

# --- Task Definition ---
resource "aws_ecs_task_definition" "backend" {
  family                   = "${var.project}-backend"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = var.backend_cpu
  memory                   = var.backend_memory
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([{
    name  = "backend"
    image = "${aws_ecr_repository.backend.repository_url}:latest"

    portMappings = [{
      containerPort = 8000
      protocol      = "tcp"
    }]

    environment = [
      { name = "ENVIRONMENT", value = "production" },
      { name = "DEBUG", value = "false" },
      # No password in the URL — backend's config.py splices it from
      # the DB_PASSWORD secret at boot. This keeps the URL stable across
      # password rotations and avoids having two sources of truth for
      # the password.
      { name = "DATABASE_URL", value = "postgresql+asyncpg://${var.db_username}@${aws_db_instance.main.endpoint}/${var.db_name}?ssl=require" },
      { name = "AWS_REGION", value = var.aws_region },
      { name = "S3_BUCKET_NAME", value = "${var.project}-documents" },
      { name = "S3_LOCAL_MODE", value = "false" },
      { name = "COGNITO_USER_POOL_ID", value = aws_cognito_user_pool.main.id },
      { name = "COGNITO_APP_CLIENT_ID", value = aws_cognito_user_pool_client.web.id },
      { name = "COGNITO_DOMAIN", value = "${var.project}.auth.${var.aws_region}.amazoncognito.com" },
      { name = "COGNITO_BYPASS", value = "false" },
      { name = "AI_MOCK_MODE", value = "false" },
      # Plan 2 LLM stack — each surface falls back to its deterministic
      # stub on agent failure (see tests/test_plan2_integration.py), so
      # flipping these on is graceful.
      { name = "AI_DISCOVERY_V2_ENABLED", value = "true" },
      { name = "AI_WORKSHOPS_V2_ENABLED", value = "true" },
      { name = "AI_MATCH_RATIONALE_V2_ENABLED", value = "true" },
      { name = "AI_STRATEGY_V2_ENABLED", value = "true" },
      { name = "AI_IDENTITY_V2_ENABLED", value = "true" },
      { name = "AI_DISCOVERY_QUERY_V2_ENABLED", value = "true" },
      { name = "AI_OUTCOME_BRIEF_V2_ENABLED", value = "true" },
      # Spec 17 §7 / 45 §13 — Inbox AI-suggested replies (InboxReplyDrafter,
      # outreach-consent-gated). No rule-based fallback: on failure the card
      # is hidden, so the inbox is fully functional with the flag off too.
      { name = "AI_INBOX_V2_ENABLED", value = "true" },
      # Spec 25 §10 / 45 §16 — "Draft with AI" campaign copy (Sonnet). Falls
      # back to an objective-keyed template stub on any failure, so the editor
      # button works with the flag off too.
      { name = "AI_CAMPAIGN_COPY_V2_ENABLED", value = "true" },
      # Spec 26 §6 / 45 §17 — SegmentBuilderNLBridge (natural-language → segment
      # rules, Sonnet). On any failure it falls back to a keyword parser, so the
      # segment builder is fully functional with the flag off too.
      { name = "AI_SEGMENT_BUILDER_V2_ENABLED", value = "true" },
      # Spec 29 §8 / 45 — InstitutionReplyDrafter (Haiku). The institution inbox
      # "AI draft" button; respects the applicant's matching consent for profile
      # context and hides the card on failure, so the inbox works with it off too.
      { name = "AI_INSTITUTION_REPLY_V2_ENABLED", value = "true" },
      # Spec 29 §8 / §14 — InboundIntentClassifier (Haiku, suggestion-only). Off
      # by default per the spec (auto-routing risks mis-routing); ship as a
      # suggestion first. Flip to "true" to surface reason-code suggestions.
      { name = "AI_INBOUND_INTENT_V2_ENABLED", value = "false" },
      # Spec 33 §9 — interview helpers: Haiku InterviewInviteDrafter ("AI draft"
      # in the Propose modal) + Sonnet InterviewScorePrefill ("AI prefill" in the
      # Score modal). Both return null on failure, so the module works with it
      # off too; enabled in prod for the assisted experience.
      { name = "AI_INTERVIEW_V2_ENABLED", value = "true" },
      # Spec 35 §6 / 45 — enrollment-yield intelligence (NextBestActionForYield,
      # Sonnet). Refines the yield dashboard's ranked actions; always falls back
      # to deterministic counts on failure, so the dashboard works with it off
      # too. YieldRiskScorer is a deterministic heuristic regardless.
      { name = "AI_YIELD_INTELLIGENCE_V2_ENABLED", value = "true" },
      # Spec 38 §5 — international-admissions agents (CredentialNormalizer +
      # CountryRequirementAdvisor). Both Haiku and always fall back to
      # deterministic logic (grading-scale mapper / default country pack), so
      # the workspace functions with it off too. AI never decides feasibility.
      { name = "AI_INTERNATIONAL_V2_ENABLED", value = "true" },
      # Spec 40 §5 / 45 — recruitment CRM intelligence (TerritoryOptimizer,
      # Sonnet). Refines per-territory travel suggestions; always falls back to
      # deterministic prior-year-yield ranking on failure. ProspectPrioritizer is
      # a deterministic apply-likelihood heuristic regardless. Prioritization +
      # planning only, never selection.
      { name = "AI_RECRUITMENT_V2_ENABLED", value = "true" },
      # Spec 41 §5 — graduate-admissions intelligence (AdvisorMatcher +
      # SoPInterestExtractor + FundingScenarioHelper). Auto-tags SoP interests,
      # adds advisor-fit rationale, and surfaces funding over-commit warnings +
      # re-mix suggestions. The deterministic baseline (advisor alignment ranking
      # + the hard over-commit block) is always on; AI never decides — matching
      # informs humans, faculty decide.
      { name = "AI_GRADUATE_V2_ENABLED", value = "true" },
      # Spec 42 §4.17 — Prompt Library behavioral coach. Attaches the inference
      # overlay (interview-readiness, competency coverage, story↔prompt matching,
      # revision priorities, practice plan) to the prompt-library summary. The
      # engine is deterministic and never 5xxes; STAR auto-detection on save runs
      # regardless. Tier documents the future LLM swap-in.
      { name = "AI_PROMPT_LIBRARY_V2_ENABLED", value = "true" },
      # Pin Claude model IDs — config.py defaults match, but pinning here
      # makes the prod surface auditable (and trivial to roll a single
      # agent class to a different model without a code deploy).
      { name = "LLM_REASONING_MODEL", value = "claude-sonnet-4-6" },
      { name = "LLM_FEATURE_MODEL", value = "claude-haiku-4-5" },
      # Spec 03 §2 + §6 — three-tier model map. Updating any of these
      # rolls forward the whole agent class without a code deploy
      # (matches the spec's "Secret update + task restart" model).
      { name = "ANTHROPIC_DEFAULT_FLAGSHIP", value = "claude-opus-4-8" },
      { name = "ANTHROPIC_DEFAULT_WORKHORSE", value = "claude-sonnet-4-6" },
      { name = "ANTHROPIC_DEFAULT_BATCH", value = "claude-haiku-4-5-20251001" },
      # Spec 03 §5/§6 — provider abstraction. anthropic is the default
      # for every agent. Per-agent overrides go in AI_PROVIDER_PER_AGENT_JSON.
      { name = "AI_PROVIDER_DEFAULT", value = "anthropic" },
      { name = "AI_PROVIDER_PER_AGENT_JSON", value = "" },
      # Spec 03 §9 — failover order. Try anthropic → openai → rule_based.
      # Per-attempt timeout for the LLM round trip.
      { name = "AI_PROVIDER_FAILOVER_CSV", value = "anthropic,openai" },
      { name = "AI_PROVIDER_FAILOVER_TIMEOUT_MS", value = "30000" },
      { name = "EMBEDDING_MODEL", value = "voyage-3-large" },
      { name = "CORS_ORIGINS", value = "[\"https://app.${var.domain_name}\"]" },
      { name = "SES_SENDER_EMAIL", value = "noreply@${var.domain_name}" },
      { name = "NOTIFICATIONS_ENABLED", value = "true" },
    ]

    secrets = [
      {
        name      = "DB_PASSWORD"
        valueFrom = aws_secretsmanager_secret.db_password.arn
      },
      {
        name      = "OPENAI_API_KEY"
        valueFrom = aws_secretsmanager_secret.openai_api_key.arn
      },
      # Claude API — the student-side LLM stack (orchestrator, extractor,
      # validator, feature emitter, rationale, workshop coach, strategy,
      # identity summary) routes through the AIClient singleton against
      # Anthropic. Without this, every agent silently falls through to the
      # rule-based stub.
      {
        name      = "ANTHROPIC_API_KEY"
        valueFrom = aws_secretsmanager_secret.anthropic_api_key.arn
      },
      # Voyage powers the dense applicant_summary embedding consumed by
      # the ML matcher. Without it, match.cosine collapses to zero and
      # the dual-score (fitness / confidence) loses one of three signals.
      {
        name      = "VOYAGE_API_KEY"
        valueFrom = aws_secretsmanager_secret.voyage_api_key.arn
      },
    ]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = aws_cloudwatch_log_group.backend.name
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "backend"
      }
    }

    healthCheck = {
      command     = ["CMD-SHELL", "curl -f http://localhost:8000/api/v1/health || exit 1"]
      interval    = 30
      timeout     = 5
      retries     = 3
      startPeriod = 60
    }
  }])
}

# --- ECS Service ---
resource "aws_ecs_service" "backend" {
  name            = "${var.project}-backend"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.backend.arn
  desired_count   = var.backend_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.private[*].id
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.backend.arn
    container_name   = "backend"
    container_port   = 8000
  }

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  depends_on = [aws_lb_listener.https]
}

# --- Auto Scaling ---
resource "aws_appautoscaling_target" "backend" {
  max_capacity       = var.backend_max_count
  min_capacity       = var.backend_min_count
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.backend.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "backend_cpu" {
  name               = "${var.project}-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.backend.resource_id
  scalable_dimension = aws_appautoscaling_target.backend.scalable_dimension
  service_namespace  = aws_appautoscaling_target.backend.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value       = 70.0
    scale_in_cooldown  = 300
    scale_out_cooldown = 60
  }
}
