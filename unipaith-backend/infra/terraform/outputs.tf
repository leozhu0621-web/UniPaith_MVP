output "gpu_8b_instance_id" {
  value       = aws_instance.gpu_8b.id
  description = "Instance ID for the 8B GPU (set as GPU_8B_INSTANCE_ID in .env)"
}

output "gpu_70b_instance_id" {
  value       = aws_instance.gpu_70b.id
  description = "Instance ID for the 70B GPU (set as GPU_70B_INSTANCE_ID in .env)"
}

output "gpu_8b_private_ip" {
  value       = aws_instance.gpu_8b.private_ip
  description = "Private IP for the 8B instance (set GPU_8B_ENDPOINT=http://<ip>:8001)"
}

output "gpu_70b_private_ip" {
  value       = aws_instance.gpu_70b.private_ip
  description = "Private IP for the 70B instance (set GPU_70B_ENDPOINT=http://<ip>:8002)"
}

output "model_weights_bucket" {
  value       = aws_s3_bucket.model_weights.bucket
  description = "S3 bucket for cached model weights"
}
