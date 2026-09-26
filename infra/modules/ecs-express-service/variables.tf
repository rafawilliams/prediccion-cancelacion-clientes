variable "service_name" {
  description = "The name of the ECS service express."
  type        = string
}

variable "image_uri" {
  description = "The URI of the Docker image to use for the ECS service."
  type        = string
}

variable "container_port" {
  description = "The port on which the container listens."
  type        = number
  default     = 3000
}
variable "health_check_path" {
  description = "The path to use for the health check."
  type        = string
  default     = "/health"
}

variable "cpu" {
  description = "Unidades de CPU para la tarea (potencias de 2, 256-4096)"
  type        = number
  default     = 256
}

variable "memory" {
  description = "Memoria en MiB para la tarea (512-8192)"
  type        = number
  default     = 512
}


variable "role_name_prefix" {
  description = "Prefijo para los nombres de los roles IAM. Si es null se usa service_name."
  type        = string
  default     = null
}
