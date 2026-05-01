# --- GitHub Actions OIDC ---
# Allows GitHub Actions to assume an IAM role using OIDC — no static AWS keys needed.

variable "github_repo" {
  description = "GitHub repo in owner/name format (e.g. acme/unipaith)"
  type        = string
  default     = "leozhu0621-web/UniPaith_MVP"
}

resource "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"

  client_id_list = ["sts.amazonaws.com"]

  # GitHub's OIDC thumbprint (stable — this is the SHA1 of GitHub's root CA)
  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1"]
}

resource "aws_iam_role" "github_actions" {
  name = "${var.project}-github-actions"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Federated = aws_iam_openid_connect_provider.github.arn
      }
      Action = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
        }
        StringLike = {
          # main branch (push-to-main → apply) AND any pull_request (plan-only)
          "token.actions.githubusercontent.com:sub" = [
            "repo:${var.github_repo}:ref:refs/heads/main",
            "repo:${var.github_repo}:pull_request",
          ]
        }
      }
    }]
  })
}

# --- Managed policies for Terraform apply (broad but scoped to common services) ---
locals {
  github_actions_managed_policies = [
    "arn:aws:iam::aws:policy/AmazonEC2FullAccess",
    "arn:aws:iam::aws:policy/AmazonRDSFullAccess",
    "arn:aws:iam::aws:policy/AmazonRoute53FullAccess",
    "arn:aws:iam::aws:policy/ElasticLoadBalancingFullAccess",
    "arn:aws:iam::aws:policy/IAMFullAccess",
    "arn:aws:iam::aws:policy/SecretsManagerReadWrite",
    "arn:aws:iam::aws:policy/AWSBackupFullAccess",
    "arn:aws:iam::aws:policy/AmazonSSMFullAccess",
    "arn:aws:iam::aws:policy/AWSCertificateManagerFullAccess",
  ]
}

resource "aws_iam_role_policy_attachment" "github_actions_managed" {
  for_each   = toset(local.github_actions_managed_policies)
  role       = aws_iam_role.github_actions.name
  policy_arn = each.value
}

# --- Inline policy for Terraform state (S3 backend + DynamoDB lock) ---
resource "aws_iam_role_policy" "github_actions_tf_state" {
  name = "terraform-state-access"
  role = aws_iam_role.github_actions.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "TerraformStateBucket"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket",
        ]
        Resource = [
          aws_s3_bucket.terraform_state.arn,
          "${aws_s3_bucket.terraform_state.arn}/*",
        ]
      },
      {
        Sid    = "TerraformStateLock"
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:DeleteItem",
          "dynamodb:DescribeTable",
        ]
        Resource = [aws_dynamodb_table.terraform_locks.arn]
      },
      {
        Sid    = "KMSForStateEncryption"
        Effect = "Allow"
        Action = [
          "kms:Decrypt",
          "kms:GenerateDataKey",
        ]
        Resource = ["*"]
      },
    ]
  })
}

resource "aws_iam_role_policy" "github_actions" {
  name = "deploy-permissions"
  role = aws_iam_role.github_actions.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "ECRAuth"
        Effect   = "Allow"
        Action   = ["ecr:GetAuthorizationToken"]
        Resource = ["*"]
      },
      {
        Sid    = "ECRPush"
        Effect = "Allow"
        Action = [
          "ecr:BatchCheckLayerAvailability",
          "ecr:InitiateLayerUpload",
          "ecr:UploadLayerPart",
          "ecr:CompleteLayerUpload",
          "ecr:PutImage",
          "ecr:BatchGetImage",
          "ecr:GetDownloadUrlForLayer",
        ]
        Resource = [aws_ecr_repository.backend.arn]
      },
      {
        Sid    = "ECSDeployBackend"
        Effect = "Allow"
        Action = [
          "ecs:UpdateService",
          "ecs:DescribeServices",
        ]
        Resource = [aws_ecs_service.backend.id]
      },
      {
        Sid      = "ECSWait"
        Effect   = "Allow"
        Action   = ["ecs:DescribeServices"]
        Resource = ["*"]
      },
      {
        Sid    = "S3FrontendDeploy"
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket",
          "s3:GetObject",
        ]
        Resource = [
          aws_s3_bucket.frontend.arn,
          "${aws_s3_bucket.frontend.arn}/*",
        ]
      },
      {
        Sid    = "CloudFrontInvalidate"
        Effect = "Allow"
        Action = [
          "cloudfront:CreateInvalidation",
          "cloudfront:ListDistributions",
        ]
        Resource = ["*"]
      },
    ]
  })
}

output "github_actions_role_arn" {
  description = "ARN to set as GH_ACTIONS_ROLE_ARN in GitHub Actions secrets"
  value       = aws_iam_role.github_actions.arn
}
