output "ecr_repository_url" {
  description = "ECR repository URL for backend Docker images"
  value       = aws_ecr_repository.backend.repository_url
}

output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint"
  value       = aws_db_instance.main.endpoint
}

output "alb_dns_name" {
  description = "ALB DNS name"
  value       = aws_lb.main.dns_name
}

output "cloudfront_domain" {
  description = "CloudFront distribution domain"
  value       = aws_cloudfront_distribution.main.domain_name
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID (for cache invalidation)"
  value       = aws_cloudfront_distribution.main.id
}

output "frontend_bucket" {
  description = "S3 bucket for frontend static files"
  value       = aws_s3_bucket.frontend.id
}

output "documents_bucket" {
  description = "S3 bucket for user document uploads"
  value       = aws_s3_bucket.documents.id
}

output "website_url" {
  description = "Live website URL"
  value       = "https://${var.domain_name}"
}

output "api_url" {
  description = "API base URL"
  value       = "https://${var.domain_name}/api/v1"
}

output "api_direct_url" {
  description = "Direct API URL via ALB"
  value       = "https://api.${var.domain_name}/api/v1"
}
