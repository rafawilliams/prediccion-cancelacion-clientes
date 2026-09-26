
output "api_url" {
  description = "URL pública generada por ECS Express Mode"
  value       = aws_ecs_express_gateway_service.this.ingress_paths
}