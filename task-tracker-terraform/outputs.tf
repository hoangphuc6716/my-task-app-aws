output "lb_dns_name" {
  description = "The DNS name of the Load Balancer"
  value       = aws_lb.alb.dns_name
}

output "ec2_public_ip" {
  description = "The public IP of the EC2 instance"
  value       = aws_eip.eip_ec2.public_ip
}

output "rds_endpoint" {
  description = "The connection endpoint for the RDS instance"
  value       = aws_db_instance.rds_postgres.endpoint
}