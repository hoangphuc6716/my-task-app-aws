resource "aws_db_subnet_group" "db_subnet_group" {
  name       = "prod-task-tracker-db-subnet"
  subnet_ids = data.aws_subnets.default.ids
}

resource "aws_db_instance" "rds_postgres" {
  allocated_storage      = 20
  engine                 = "postgres"
  engine_version         = "16.3"
  instance_class         = "db.t3.micro"
  db_name                = "tasktrackerprod"
  username               = var.db_username
  password               = var.db_password
  vpc_security_group_ids = [aws_security_group.sg_rds.id]
  db_subnet_group_name   = aws_db_subnet_group.db_subnet_group.name
  skip_final_snapshot    = true
  publicly_accessible    = false
}