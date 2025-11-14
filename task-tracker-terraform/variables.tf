variable "aws_region" {
  description = "The AWS region to deploy to"
  type        = string
}

variable "key_pair_name" {
  description = "Name of the EC2 Key Pair (must exist in the target region)"
  type        = string
}

variable "db_password" {
  description = "Password for the RDS database"
  type        = string
  sensitive   = true
}

variable "db_username" {
  description = "Username for the RDS database"
  type        = string
  default     = "postgres"
}