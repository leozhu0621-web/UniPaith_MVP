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

# --- OpenAI API key ---
resource "aws_secretsmanager_secret" "openai_api_key" {
  name                    = "${var.project}/${var.environment}/openai-api-key"
  recovery_window_in_days = 7
}

resource "aws_secretsmanager_secret_version" "openai_api_key" {
  secret_id     = aws_secretsmanager_secret.openai_api_key.id
  secret_string = var.openai_api_key
}
