# Self-hosted Qwen on vLLM (AI Structure) — the open-source backend LLM for the
# ML / extraction agents (the Claude<->Qwen boundary keeps every human-facing
# surface on Claude regardless). ONE g5.xlarge (NVIDIA A10G 24GB) in a PRIVATE
# subnet, reachable ONLY from the backend ECS tasks; serves the OpenAI-compatible
# API on :8000. ~$730/mo on-demand. Fits the account's 4-vCPU GPU quota exactly.
#
# Graceful by design: if the box is mid-boot / unhealthy, the backend's provider
# guard + failover (anthropic) serve the request, so the app never breaks on it.

data "aws_ami" "dlami_gpu" {
  most_recent = true
  owners      = ["amazon"]
  filter {
    name   = "name"
    values = ["Deep Learning OSS Nvidia Driver AMI GPU PyTorch*Ubuntu 22.04*"]
  }
}

resource "aws_security_group" "qwen_vllm" {
  name_prefix = "${var.project}-qwen-"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_tasks.id] # backend ECS tasks only
    description     = "vLLM OpenAI API — backend ECS only"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"] # model + image pull via the VPC NAT
  }

  tags = { Name = "${var.project}-qwen-sg" }

  lifecycle {
    create_before_destroy = true
  }
}

# SSM-only access (no SSH key, no public IP) for verification/ops.
resource "aws_iam_role" "qwen_vllm" {
  name = "${var.project}-qwen-vllm"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "qwen_ssm" {
  role       = aws_iam_role.qwen_vllm.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "qwen_vllm" {
  name = "${var.project}-qwen-vllm"
  role = aws_iam_role.qwen_vllm.name
}

resource "aws_instance" "qwen_vllm" {
  ami                    = data.aws_ami.dlami_gpu.id
  instance_type          = "g5.xlarge"
  subnet_id              = "subnet-0b62e9947b9d73300" # private, us-east-1a (offers g5.xlarge)
  vpc_security_group_ids = [aws_security_group.qwen_vllm.id]
  iam_instance_profile   = aws_iam_instance_profile.qwen_vllm.name

  root_block_device {
    volume_size = 150
    volume_type = "gp3"
  }

  # DLAMI ships Docker + the NVIDIA container runtime. Serve Qwen2.5-7B-Instruct
  # on the OpenAI-compatible API; the model (public, ~15GB) pulls from HuggingFace
  # on first boot. Tuned to fit the 24GB A10G (15GB weights + KV cache headroom).
  user_data = <<-EOF
    #!/bin/bash
    set -euxo pipefail
    mkdir -p /data/hf
    docker run -d --restart unless-stopped --gpus all -p 8000:8000 \
      -v /data/hf:/root/.cache/huggingface \
      --name vllm vllm/vllm-openai:latest \
      --model Qwen/Qwen2.5-7B-Instruct \
      --max-model-len 8192 \
      --gpu-memory-utilization 0.92
  EOF

  tags = { Name = "${var.project}-qwen-vllm" }
}

output "qwen_vllm_private_ip" {
  value       = aws_instance.qwen_vllm.private_ip
  description = "Private IP of the self-hosted Qwen/vLLM box (backend QWEN_BASE_URL)."
}
