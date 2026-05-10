# --- Database password ---
resource "random_password" "db_password" {
  length  = 32
  special = false # asyncpg connection strings don't handle some special chars well
}

resource "aws_secretsmanager_secret" "db_password" {
  name                    = "${var.project}/${var.environment}/db-password"
  recovery_window_in_days = 7
}

resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id     = aws_secretsmanager_secret.db_password.id
  secret_string = random_password.db_password.result
  # Manual rotations (e.g. via the AWS console or `aws rds modify-db-instance`)
  # write a new value here. Ignore drift so a Terraform apply doesn't
  # reset the secret back to the bootstrap-time random_password value.
  lifecycle {
    ignore_changes = [secret_string]
  }
}

# --- Application secrets ---
resource "random_password" "app_secret" {
  length  = 64
  special = false
}

resource "aws_secretsmanager_secret" "app_secret" {
  name                    = "${var.project}/${var.environment}/app-secret"
  recovery_window_in_days = 7
}

resource "aws_secretsmanager_secret_version" "app_secret" {
  secret_id     = aws_secretsmanager_secret.app_secret.id
  secret_string = random_password.app_secret.result
}

# --- OpenAI API key (legacy — used by offline crawler/extractor only) ---
resource "aws_secretsmanager_secret" "openai_api_key" {
  name                    = "${var.project}/${var.environment}/openai-api-key"
  recovery_window_in_days = 7
}

resource "aws_secretsmanager_secret_version" "openai_api_key" {
  secret_id     = aws_secretsmanager_secret.openai_api_key.id
  secret_string = var.openai_api_key
}

# --- Anthropic API key (primary user-facing LLM — Plan 2) ---
resource "aws_secretsmanager_secret" "anthropic_api_key" {
  name                    = "${var.project}/${var.environment}/anthropic-api-key"
  recovery_window_in_days = 7
}

resource "aws_secretsmanager_secret_version" "anthropic_api_key" {
  secret_id     = aws_secretsmanager_secret.anthropic_api_key.id
  secret_string = var.anthropic_api_key
}

# --- Voyage embeddings API key (paired with Anthropic for the new feature pipeline) ---
resource "aws_secretsmanager_secret" "voyage_api_key" {
  name                    = "${var.project}/${var.environment}/voyage-api-key"
  recovery_window_in_days = 7
}

resource "aws_secretsmanager_secret_version" "voyage_api_key" {
  secret_id     = aws_secretsmanager_secret.voyage_api_key.id
  secret_string = var.voyage_api_key
}
