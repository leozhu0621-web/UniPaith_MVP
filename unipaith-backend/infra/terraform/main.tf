terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Store state in S3 (uncomment and configure for production)
  # backend "s3" {
  #   bucket = "unipaith-terraform-state"
  #   key    = "gpu-infra/terraform.tfstate"
  #   region = "us-east-1"
  # }
}

provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  default = "us-east-1"
}

variable "project" {
  default = "unipaith"
}

variable "environment" {
  default = "staging"
}

variable "backend_sg_id" {
  description = "Security group ID of the backend server (to allow GPU access)"
  type        = string
  default     = ""
}

variable "vpc_id" {
  description = "VPC ID where GPU instances will be launched"
  type        = string
}

variable "subnet_id" {
  description = "Private subnet ID for GPU instances"
  type        = string
}

variable "key_name" {
  description = "SSH key pair name for GPU instances"
  type        = string
  default     = "unipaith-gpu"
}

# Budget alert email
variable "alert_email" {
  description = "Email for budget/alarm notifications"
  type        = string
}
