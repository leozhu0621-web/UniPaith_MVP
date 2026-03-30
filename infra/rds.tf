# --- Security Group ---
resource "aws_security_group" "rds" {
  name_prefix = "${var.project}-rds-"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_tasks.id]
    description     = "PostgreSQL from ECS tasks"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.project}-rds-sg" }

  lifecycle {
    create_before_destroy = true
  }
}

# --- Subnet Group ---
resource "aws_db_subnet_group" "main" {
  name       = "${var.project}-db-subnet"
  subnet_ids = aws_subnet.private[*].id

  tags = { Name = "${var.project}-db-subnet" }
}

# --- Parameter Group (enable pgvector) ---
resource "aws_db_parameter_group" "postgres16" {
  name_prefix = "${var.project}-pg16-"
  family      = "postgres16"

  parameter {
    name         = "shared_preload_libraries"
    value        = "pg_stat_statements"
    apply_method = "pending-reboot"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# --- RDS Instance ---
resource "aws_db_instance" "main" {
  identifier = "${var.project}-db"

  engine         = "postgres"
  engine_version = "16.4"
  instance_class = var.db_instance_class

  db_name  = var.db_name
  username = var.db_username
  password = random_password.db_password.result

  allocated_storage     = var.db_allocated_storage
  max_allocated_storage = var.db_max_allocated_storage
  storage_encrypted     = true

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  parameter_group_name   = aws_db_parameter_group.postgres16.name

  multi_az            = false # set to true for HA ($140/mo extra)
  publicly_accessible = false

  backup_retention_period = 7
  backup_window           = "03:00-04:00"
  maintenance_window      = "Mon:04:00-Mon:05:00"

  skip_final_snapshot       = false
  final_snapshot_identifier = "${var.project}-db-final"
  deletion_protection       = true

  performance_insights_enabled = true

  tags = { Name = "${var.project}-db" }
}

# Note: After RDS is created, connect and run:
#   CREATE EXTENSION IF NOT EXISTS vector;
# This is also handled by Alembic migrations.
