terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

resource "aws_iam_role" "ecs_task_execution_role" {
  name = "churn-api-ecs-task-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role" "ecs_infrastructure_role" {
  name = "churn-api-ecs-infrastructure-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ecs.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_infrastructure_policy" {
  role       = aws_iam_role.ecs_infrastructure_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSInfrastructureRoleforExpressGatewayServices"
}


resource "aws_ecs_express_gateway_service" "churn_api" {
  service_name = "churn-prediction-api"

  primary_container {
    image          = "504556110660.dkr.ecr.us-east-1.amazonaws.com/churn-prediction-api:latest"
    container_port = 8000
  }

  execution_role_arn      = aws_iam_role.ecs_task_execution_role.arn
  infrastructure_role_arn = aws_iam_role.ecs_infrastructure_role.arn

  cpu               = 256
  memory            = 512
  health_check_path = "/health"

  depends_on = [
    aws_iam_role_policy_attachment.ecs_task_execution_policy,
    aws_iam_role_policy_attachment.ecs_infrastructure_policy
  ]
}

output "api_url" {
  description = "URL pública de la API generada por ECS Express Mode"
  value       = aws_ecs_express_gateway_service.churn_api.ingress_paths
}


