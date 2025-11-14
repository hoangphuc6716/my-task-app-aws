resource "aws_eip" "eip_ec2" {
  domain = "vpc"
}

data "aws_ami" "amazon_linux_2" {
  most_recent = true
  owners      = ["amazon"]
  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
}

resource "aws_instance" "app_server" {
  ami           = data.aws_ami.amazon_linux_2.id
  instance_type = "t3.micro"
  key_name      = var.key_pair_name
  vpc_security_group_ids = [aws_security_group.sg_ec2.id]
  subnet_id     = data.aws_subnets.default.ids[0]

  user_data = <<-EOF
              #!/bin/bash
              yum update -y
              yum install -y docker
              systemctl start docker
              systemctl enable docker
              usermod -aG docker ec2-user
              EOF

  tags = {
    Name = "Task-Tracker-Server-Prod"
  }
}

resource "aws_eip_association" "eip_assoc" {
  # SỬA LỖI TẠI ĐÂY:
  instance_id   = aws_instance.app_server.id 
  allocation_id = aws_eip.eip_ec2.id
}