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
  secret_id = aws_secretsmanager_secret.anthropic_api_key.id
  # Bootstrap with the var if provided, otherwise a placeholder so the
  # apply doesn't fail when the GH Actions secret isn't set. Real value
  # is rotated in via the AWS console / `aws secretsmanager put-secret-value`
  # and ignore_changes prevents Terraform from clobbering it on next apply.
  secret_string = coalesce(var.anthropic_api_key, "REPLACE_ME_VIA_AWS_CONSOLE")
  lifecycle {
    ignore_changes = [secret_string]
  }
}

# --- UniPaith MCP data-API key (single bearer for the /mcp endpoint) ---
# One key that grants the Claude platform agent ALL-DATA access to UniPaith
# (read/write any student). Real value is set via
# `aws secretsmanager put-secret-value`; ignore_changes keeps Terraform off it.
resource "aws_secretsmanager_secret" "mcp_api_key" {
  name                    = "${var.project}/${var.environment}/mcp-api-key"
  recovery_window_in_days = 7
}

resource "aws_secretsmanager_secret_version" "mcp_api_key" {
  secret_id     = aws_secretsmanager_secret.mcp_api_key.id
  secret_string = "REPLACE_ME_VIA_AWS_CONSOLE" # pragma: allowlist secret
  lifecycle {
    ignore_changes = [secret_string]
  }
}

# --- Voyage embeddings API key (paired with Anthropic for the new feature pipeline) ---
resource "aws_secretsmanager_secret" "voyage_api_key" {
  name                    = "${var.project}/${var.environment}/voyage-api-key"
  recovery_window_in_days = 7
}

resource "aws_secretsmanager_secret_version" "voyage_api_key" {
  secret_id     = aws_secretsmanager_secret.voyage_api_key.id
  secret_string = coalesce(var.voyage_api_key, "REPLACE_ME_VIA_AWS_CONSOLE")
  lifecycle {
    ignore_changes = [secret_string]
  }
}

# --- Airtable personal access token (Prompt Library sync) ---
# Read-only PAT (data.records:read + schema.bases:read) granted to the
# "UniPaith Prompt Library" base (appWT0yIT31IJu01R). Powers the manual
# POST /ops/airtable/sync that pulls prompt/template edits into the DB.
# Bootstrap with a placeholder so apply never fails; the real token is set
# out-of-band via `aws secretsmanager put-secret-value` (or the AWS console)
# and ignore_changes keeps Terraform from clobbering it. The sync endpoint is
# manual + X-Ops-Token-guarded, so the placeholder never triggers a live call.
resource "aws_secretsmanager_secret" "airtable_api_key" {
  name                    = "${var.project}/${var.environment}/airtable-api-key"
  recovery_window_in_days = 7
}

resource "aws_secretsmanager_secret_version" "airtable_api_key" {
  secret_id     = aws_secretsmanager_secret.airtable_api_key.id
  secret_string = "REPLACE_ME_VIA_AWS_CONSOLE" # pragma: allowlist secret
  lifecycle {
    ignore_changes = [secret_string]
  }
}
