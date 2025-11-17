# File: outputs.tf

output "lb_dns_name" {
  description = "The DNS name of the Load Balancer"
  value       = aws_lb.alb.dns_name
}

output "rds_endpoint" {
  description = "The connection endpoint for the RDS instance"
  value       = aws_db_instance.rds_postgres.endpoint
}