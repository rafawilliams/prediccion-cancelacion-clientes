locals {
  role_prefix = coalesce(var.role_name_prefix, var.service_name)
}


resource "aws_iam_role" "ecs_task_execution_role" {
  name = "${local.role_prefix}-task-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      },
    ]
  })

}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_role_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role" "ecs_infrastructure_role" {
  name = "${local.role_prefix}-infrastructure-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs.amazonaws.com"
        }
      },
    ]
  })

}

resource "aws_iam_role_policy_attachment" "ecs_infrastructure_role_policy" {
  role       = aws_iam_role.ecs_infrastructure_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSInfrastructureRoleforExpressGatewayServices"
}

resource "aws_ecs_express_gateway_service" "this" {
  service_name = var.service_name

  primary_container {
    image          = var.image_uri
    container_port = var.container_port
  }

  execution_role_arn      = aws_iam_role.ecs_task_execution_role.arn
  infrastructure_role_arn = aws_iam_role.ecs_infrastructure_role.arn

  cpu               = var.cpu
  memory            = var.memory
  health_check_path = var.health_check_path

  depends_on = [
    aws_iam_role_policy_attachment.ecs_task_execution_role_policy,
    aws_iam_role_policy_attachment.ecs_infrastructure_role_policy
  ]

}

# Renombres del refactor: conservan los recursos existentes en el estado
moved {
  from = aws_iam_role_policy_attachment.ecs_task_execution_policy
  to   = aws_iam_role_policy_attachment.ecs_task_execution_role_policy
}

moved {
  from = aws_iam_role_policy_attachment.ecs_infrastructure_policy
  to   = aws_iam_role_policy_attachment.ecs_infrastructure_role_policy
}
