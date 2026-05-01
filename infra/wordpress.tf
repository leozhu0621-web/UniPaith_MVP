# =============================================================================
# WordPress on EC2 + RDS MySQL — for the marketing landing at unipaith.co
#
# Architecture:
#   - Single EC2 (Amazon Linux 2023) in a public subnet, hardened, SSM-only access
#   - User-data installs Apache + PHP 8.3 + WordPress, reads RDS creds from
#     Secrets Manager and writes wp-config.php
#   - Single-AZ RDS MySQL 8.0 (db.t4g.micro) in the existing private subnets
#   - Existing ALB host-routes unipaith.co + www.unipaith.co to a new TG
#   - Existing ALB cert already has unipaith.co + *.unipaith.co as SANs (see dns.tf)
#   - Daily AMI snapshots via AWS Backup, 7-day retention
# =============================================================================

# --- Latest Amazon Linux 2023 AMI (no marketplace subscription needed) ---
data "aws_ami" "amazon_linux_2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"]
  }

  filter {
    name   = "architecture"
    values = ["x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# --- Security Groups ---
resource "aws_security_group" "wordpress" {
  name_prefix = "${var.project}-wp-"
  vpc_id      = aws_vpc.main.id
  description = "WordPress EC2 - only ALB can hit port 80"

  ingress {
    from_port       = 80
    to_port         = 80
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
    description     = "HTTP from ALB"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "All outbound (yum, GitHub, Secrets Manager, etc.)"
  }

  tags = { Name = "${var.project}-wp-sg" }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_security_group" "wp_db" {
  name_prefix = "${var.project}-wp-db-"
  vpc_id      = aws_vpc.main.id
  description = "WordPress MySQL - only WP EC2 can connect"

  ingress {
    from_port       = 3306
    to_port         = 3306
    protocol        = "tcp"
    security_groups = [aws_security_group.wordpress.id]
    description     = "MySQL from WP EC2"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.project}-wp-db-sg" }

  lifecycle {
    create_before_destroy = true
  }
}

# --- WordPress RDS MySQL (single-AZ, separate from app's Postgres) ---
resource "random_password" "wp_db_password" {
  length  = 32
  special = false
}

resource "aws_db_subnet_group" "wp" {
  name       = "${var.project}-wp-db-subnet"
  subnet_ids = aws_subnet.private[*].id

  tags = { Name = "${var.project}-wp-db-subnet" }
}

resource "aws_db_instance" "wordpress" {
  identifier = "${var.project}-wp-db"

  engine         = "mysql"
  engine_version = "8.0"
  instance_class = var.wp_db_instance_class

  db_name  = "wordpress"
  username = "wpadmin"
  password = random_password.wp_db_password.result

  allocated_storage     = 20
  max_allocated_storage = 50
  storage_type          = "gp3"
  storage_encrypted     = true

  db_subnet_group_name   = aws_db_subnet_group.wp.name
  vpc_security_group_ids = [aws_security_group.wp_db.id]

  multi_az            = false
  publicly_accessible = false

  backup_retention_period = 7
  backup_window           = "03:00-04:00"
  maintenance_window      = "Mon:04:00-Mon:05:00"

  skip_final_snapshot       = false
  final_snapshot_identifier = "${var.project}-wp-db-final"
  deletion_protection       = true

  tags = { Name = "${var.project}-wp-db" }
}

# --- Secret with the connection string for the EC2 user-data ---
resource "aws_secretsmanager_secret" "wp_db" {
  name                    = "${var.project}/${var.environment}/wp-db"
  recovery_window_in_days = 7
}

resource "aws_secretsmanager_secret_version" "wp_db" {
  secret_id = aws_secretsmanager_secret.wp_db.id
  secret_string = jsonencode({
    host     = aws_db_instance.wordpress.address
    port     = aws_db_instance.wordpress.port
    dbname   = aws_db_instance.wordpress.db_name
    username = aws_db_instance.wordpress.username
    password = random_password.wp_db_password.result
  })
}

# --- IAM Role for the EC2 (SSM access + read WP DB secret + write to S3 backups) ---
resource "aws_iam_role" "wordpress_ec2" {
  name = "${var.project}-wp-ec2"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "wp_ssm" {
  role       = aws_iam_role.wordpress_ec2.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_role_policy" "wp_secrets_read" {
  name = "wp-db-secret-read"
  role = aws_iam_role.wordpress_ec2.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["secretsmanager:GetSecretValue"]
      Resource = [aws_secretsmanager_secret.wp_db.arn]
    }]
  })
}

resource "aws_iam_instance_profile" "wordpress_ec2" {
  name = "${var.project}-wp-ec2"
  role = aws_iam_role.wordpress_ec2.name
}

# --- User-data script: install WP on first boot ---
locals {
  wordpress_user_data = <<-EOT
    #!/bin/bash
    set -euxo pipefail

    # Logs
    exec > >(tee /var/log/wp-bootstrap.log | logger -t wp-bootstrap -s 2>/dev/console) 2>&1

    # Packages
    dnf update -y
    dnf install -y httpd php php-mysqlnd php-fpm php-json php-mbstring php-xml php-gd \
                   php-curl php-zip php-intl php-opcache php-imagick mariadb105 \
                   jq awscli git tar

    systemctl enable httpd

    # Pull WP DB credentials from Secrets Manager
    SECRET_ARN="${aws_secretsmanager_secret.wp_db.arn}"
    REGION="${var.aws_region}"
    SECRET=$(aws secretsmanager get-secret-value --secret-id "$SECRET_ARN" --region "$REGION" --query SecretString --output text)
    DB_HOST=$(echo "$SECRET" | jq -r .host)
    DB_PORT=$(echo "$SECRET" | jq -r .port)
    DB_NAME=$(echo "$SECRET" | jq -r .dbname)
    DB_USER=$(echo "$SECRET" | jq -r .username)
    DB_PASS=$(echo "$SECRET" | jq -r .password)

    # Download latest WordPress
    cd /tmp
    curl -fsSL https://wordpress.org/latest.tar.gz | tar -xz
    mkdir -p /var/www/html
    cp -R wordpress/* /var/www/html/
    rm -rf /tmp/wordpress

    # Generate wp-config.php
    SALTS=$(curl -fsSL https://api.wordpress.org/secret-key/1.1/salt/)
    cat > /var/www/html/wp-config.php <<PHP
    <?php
    define( 'DB_NAME', '$DB_NAME' );
    define( 'DB_USER', '$DB_USER' );
    define( 'DB_PASSWORD', '$DB_PASS' );
    define( 'DB_HOST', '$DB_HOST:$DB_PORT' );
    define( 'DB_CHARSET', 'utf8mb4' );
    define( 'DB_COLLATE', '' );
    \$table_prefix = 'wp_';

    $SALTS

    // Behind the ALB, so WP needs to know the real protocol/host
    if ( isset( \$_SERVER['HTTP_X_FORWARDED_PROTO'] ) && \$_SERVER['HTTP_X_FORWARDED_PROTO'] === 'https' ) {
        \$_SERVER['HTTPS'] = 'on';
    }
    define( 'WP_HOME', 'https://${var.domain_name}' );
    define( 'WP_SITEURL', 'https://${var.domain_name}' );

    // Hardening
    define( 'DISALLOW_FILE_EDIT', true );
    define( 'WP_AUTO_UPDATE_CORE', 'minor' );

    if ( ! defined( 'ABSPATH' ) ) {
        define( 'ABSPATH', __DIR__ . '/' );
    }
    require_once ABSPATH . 'wp-settings.php';
    PHP

    # Permissions
    chown -R apache:apache /var/www/html
    find /var/www/html -type d -exec chmod 755 {} \;
    find /var/www/html -type f -exec chmod 644 {} \;

    # Apache vhost — listen on :80, set X-Forwarded-Proto handling
    cat > /etc/httpd/conf.d/wordpress.conf <<'APACHE'
    <VirtualHost *:80>
        DocumentRoot /var/www/html
        <Directory /var/www/html>
            AllowOverride All
            Require all granted
        </Directory>
        ErrorLog /var/log/httpd/wp-error.log
        CustomLog /var/log/httpd/wp-access.log combined
    </VirtualHost>
    APACHE

    # Reload and start
    systemctl restart httpd

    echo "WordPress bootstrap complete at $(date)"
  EOT
}

# --- WordPress EC2 Instance ---
resource "aws_instance" "wordpress" {
  ami                  = data.aws_ami.amazon_linux_2023.id
  instance_type        = var.wordpress_instance_type
  subnet_id            = aws_subnet.public[0].id
  iam_instance_profile = aws_iam_instance_profile.wordpress_ec2.name

  vpc_security_group_ids      = [aws_security_group.wordpress.id]
  associate_public_ip_address = true

  user_data                   = local.wordpress_user_data
  user_data_replace_on_change = false

  root_block_device {
    volume_size           = 30
    volume_type           = "gp3"
    encrypted             = true
    delete_on_termination = false
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 2
  }

  tags = {
    Name        = "${var.project}-wordpress"
    BackupPlan  = "daily"
    Application = "wordpress"
  }

  lifecycle {
    ignore_changes = [ami, user_data]
  }

  depends_on = [aws_db_instance.wordpress, aws_secretsmanager_secret_version.wp_db]
}

resource "aws_eip" "wordpress" {
  instance = aws_instance.wordpress.id
  domain   = "vpc"

  tags = { Name = "${var.project}-wp-eip" }
}

# --- ALB Target Group + Listener Rule ---
resource "aws_lb_target_group" "wordpress" {
  name        = "${var.project}-wp-tg"
  port        = 80
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "instance"

  health_check {
    path                = "/wp-login.php"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    matcher             = "200,301,302"
  }

  deregistration_delay = 30
}

resource "aws_lb_target_group_attachment" "wordpress" {
  target_group_arn = aws_lb_target_group.wordpress.arn
  target_id        = aws_instance.wordpress.id
  port             = 80
}

resource "aws_lb_listener_rule" "wordpress" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 100

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.wordpress.arn
  }

  condition {
    host_header {
      values = [var.domain_name, "www.${var.domain_name}"]
    }
  }
}

# --- AWS Backup: daily snapshots, 7-day retention ---
resource "aws_backup_vault" "wordpress" {
  name = "${var.project}-wp-backup"
}

resource "aws_iam_role" "backup" {
  name = "${var.project}-backup"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "backup.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "backup" {
  role       = aws_iam_role.backup.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForBackup"
}

resource "aws_backup_plan" "wordpress" {
  name = "${var.project}-wp-daily"

  rule {
    rule_name         = "daily"
    target_vault_name = aws_backup_vault.wordpress.name
    schedule          = "cron(0 5 ? * * *)" # 5 AM UTC daily
    start_window      = 60
    completion_window = 240

    lifecycle {
      delete_after = 7
    }
  }
}

resource "aws_backup_selection" "wordpress" {
  iam_role_arn = aws_iam_role.backup.arn
  name         = "${var.project}-wp-selection"
  plan_id      = aws_backup_plan.wordpress.id

  selection_tag {
    type  = "STRINGEQUALS"
    key   = "BackupPlan"
    value = "daily"
  }
}
