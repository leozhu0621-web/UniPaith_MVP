# Security group for GPU instances — only accessible from backend
resource "aws_security_group" "gpu" {
  name_prefix = "${var.project}-gpu-"
  vpc_id      = var.vpc_id
  description = "GPU instances - vLLM serving"

  # vLLM port for 8B model
  ingress {
    from_port       = 8001
    to_port         = 8001
    protocol        = "tcp"
    security_groups = var.backend_sg_id != "" ? [var.backend_sg_id] : []
    cidr_blocks     = var.backend_sg_id == "" ? ["10.0.0.0/8"] : []
    description     = "vLLM 8B model"
  }

  # vLLM port for embedding model
  ingress {
    from_port       = 8003
    to_port         = 8003
    protocol        = "tcp"
    security_groups = var.backend_sg_id != "" ? [var.backend_sg_id] : []
    cidr_blocks     = var.backend_sg_id == "" ? ["10.0.0.0/8"] : []
    description     = "vLLM embedding model"
  }

  # vLLM port for 70B model
  ingress {
    from_port       = 8002
    to_port         = 8002
    protocol        = "tcp"
    security_groups = var.backend_sg_id != "" ? [var.backend_sg_id] : []
    cidr_blocks     = var.backend_sg_id == "" ? ["10.0.0.0/8"] : []
    description     = "vLLM 70B model"
  }

  # SSH for debugging
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"]
    description = "SSH from VPC"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "All outbound"
  }

  tags = {
    Name    = "${var.project}-gpu"
    Project = var.project
    Env     = var.environment
  }
}

# --- g5.xlarge: Always-on, serves Llama 3.1 8B + nomic-embed-text ---

resource "aws_instance" "gpu_8b" {
  ami           = data.aws_ami.deep_learning.id
  instance_type = "g5.xlarge"
  subnet_id     = var.subnet_id
  key_name      = var.key_name

  vpc_security_group_ids = [aws_security_group.gpu.id]

  root_block_device {
    volume_size = 100  # GB — enough for model weights + OS
    volume_type = "gp3"
  }

  user_data = base64encode(templatefile("${path.module}/../scripts/setup_vllm_8b.sh", {
    s3_bucket = aws_s3_bucket.model_weights.bucket
  }))

  tags = {
    Name    = "${var.project}-gpu-8b"
    Project = var.project
    Env     = var.environment
    Role    = "llm-8b"
  }
}

# --- g5.12xlarge: On-demand, serves Llama 3.1 70B ---

resource "aws_instance" "gpu_70b" {
  ami           = data.aws_ami.deep_learning.id
  instance_type = "g5.12xlarge"
  subnet_id     = var.subnet_id
  key_name      = var.key_name

  vpc_security_group_ids = [aws_security_group.gpu.id]

  root_block_device {
    volume_size = 200  # GB — 70B model is ~140GB in fp16
    volume_type = "gp3"
  }

  user_data = base64encode(templatefile("${path.module}/../scripts/setup_vllm_70b.sh", {
    s3_bucket = aws_s3_bucket.model_weights.bucket
  }))

  tags = {
    Name    = "${var.project}-gpu-70b"
    Project = var.project
    Env     = var.environment
    Role    = "llm-70b"
  }

  # Start in stopped state — backend starts it on-demand
  lifecycle {
    ignore_changes = [instance_state]
  }
}

# Use AWS Deep Learning AMI (Ubuntu, includes NVIDIA drivers + CUDA)
data "aws_ami" "deep_learning" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["Deep Learning AMI GPU PyTorch * (Ubuntu 22.04) *"]
  }

  filter {
    name   = "state"
    values = ["available"]
  }
}

# S3 bucket for caching model weights (faster than downloading from HuggingFace)
resource "aws_s3_bucket" "model_weights" {
  bucket = "${var.project}-model-weights-${var.environment}"

  tags = {
    Project = var.project
    Env     = var.environment
  }
}
