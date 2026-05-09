variable "project" {
  description = "Project name used for resource naming"
  type        = string
  default     = "unipaith"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "production"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "domain_name" {
  description = "Primary domain name"
  type        = string
  default     = "unipaith.co"
}

# --- VPC ---
variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

# --- RDS ---
variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t4g.medium"
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "unipaith"
}

variable "db_username" {
  description = "Database master username"
  type        = string
  default     = "unipaith_admin"
}

variable "db_allocated_storage" {
  description = "RDS allocated storage in GB"
  type        = number
  default     = 100
}

variable "db_max_allocated_storage" {
  description = "RDS max autoscaling storage in GB"
  type        = number
  default     = 200
}

# --- ECS ---
variable "backend_cpu" {
  description = "Fargate task CPU units (1024 = 1 vCPU)"
  type        = number
  default     = 2048
}

variable "backend_memory" {
  description = "Fargate task memory in MB"
  type        = number
  default     = 4096
}

variable "backend_desired_count" {
  description = "Number of backend tasks"
  type        = number
  default     = 1
}

variable "backend_min_count" {
  description = "Minimum backend tasks for auto-scaling"
  type        = number
  default     = 1
}

variable "backend_max_count" {
  description = "Maximum backend tasks for auto-scaling"
  type        = number
  default     = 8
}

# --- OpenAI (legacy — offline crawler/extractor only) ---
variable "openai_api_key" {
  description = "OpenAI API key — used by the offline crawler/extractor only. User-facing AI uses Anthropic."
  type        = string
  sensitive   = true
}

# --- Anthropic (primary user-facing LLM, Plan 2) ---
variable "anthropic_api_key" {
  description = "Anthropic API key — Sonnet 4.6 + Haiku 4.5 power the Discovery / Match / Workshop agents."
  type        = string
  sensitive   = true
  default     = ""
}

# --- Voyage (embeddings, paired with Anthropic) ---
variable "voyage_api_key" {
  description = "Voyage AI API key — voyage-3-large 1024-d embeddings for the new feature-vector pipeline."
  type        = string
  sensitive   = true
  default     = ""
}
