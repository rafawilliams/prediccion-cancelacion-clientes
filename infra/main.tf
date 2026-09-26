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

# La URL del repositorio se resuelve en AWS para no dejar el ID de cuenta en el código
data "aws_ecr_repository" "api" {
  name = "churn-prediction-api"
}

module "churn-prediction-api" {
  source = "./modules/ecs-express-service"

  service_name   = "churn-prediction-api"
  image_uri      = "${data.aws_ecr_repository.api.repository_url}:latest"
  container_port = 8000
  cpu            = 256
  memory         = 512

  # Los roles ya existen en AWS con este prefijo; cambiarlo fuerza su reemplazo
  role_name_prefix = "churn-api-ecs"
}

moved {
  from = module.churn_api
  to   = module.churn-prediction-api
}

output "api_url" {
  description = "URL pública de la API generada por ECS Express Mode"
  value       = module.churn-prediction-api.api_url
}


