# --- Cognito User Pool ---
resource "aws_cognito_user_pool" "main" {
  name = "${var.project}-users"

  # Sign-in with email
  username_attributes      = ["email"]
  auto_verified_attributes = ["email"]

  password_policy {
    minimum_length    = 8
    require_lowercase = true
    require_numbers   = true
    require_symbols   = false
    require_uppercase = true
  }

  # Email verification
  verification_message_template {
    default_email_option = "CONFIRM_WITH_CODE"
    email_subject        = "UniPaith - Verify your email"
    email_message        = "Your verification code is {####}"
  }

  schema {
    name                = "email"
    attribute_data_type = "String"
    required            = true
    mutable             = true

    string_attribute_constraints {
      min_length = 1
      max_length = 256
    }
  }

  schema {
    name                = "name"
    attribute_data_type = "String"
    required            = true
    mutable             = true

    string_attribute_constraints {
      min_length = 1
      max_length = 256
    }
  }

  # Use SES for email delivery (instead of Cognito default)
  email_configuration {
    email_sending_account = "DEVELOPER"
    from_email_address    = "UniPaith <noreply@${var.domain_name}>"
    source_arn            = aws_ses_email_identity.noreply.arn
  }

  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
  }

  tags = { Name = "${var.project}-user-pool" }
}

# --- Cognito App Client ---
resource "aws_cognito_user_pool_client" "web" {
  name         = "${var.project}-web"
  user_pool_id = aws_cognito_user_pool.main.id

  generate_secret = false # SPA client — no secret

  explicit_auth_flows = [
    "ALLOW_USER_SRP_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_USER_PASSWORD_AUTH",
  ]

  supported_identity_providers = ["COGNITO"]

  callback_urls = [
    "https://app.${var.domain_name}/auth/callback",
  ]

  logout_urls = [
    "https://app.${var.domain_name}/login",
  ]

  access_token_validity  = 1  # hours
  id_token_validity      = 1  # hours
  refresh_token_validity = 30 # days

  token_validity_units {
    access_token  = "hours"
    id_token      = "hours"
    refresh_token = "days"
  }
}

# --- Cognito Domain ---
resource "aws_cognito_user_pool_domain" "main" {
  domain       = var.project # auth hosted UI at unipaith.auth.us-east-1.amazoncognito.com
  user_pool_id = aws_cognito_user_pool.main.id
}
