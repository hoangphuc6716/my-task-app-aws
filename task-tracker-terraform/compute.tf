# File: compute.tf

# 1. Lấy AMI Amazon Linux 2 mới nhất
data "aws_ami" "amazon_linux_2" {
  most_recent = true
  owners      = ["amazon"]
  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
}

# 2. Tạo Launch Template (Khuôn mẫu cấu hình cho Server)
resource "aws_launch_template" "app_lt" {
  name_prefix   = "prod-task-tracker-lt-"
  image_id      = data.aws_ami.amazon_linux_2.id
  instance_type = "t3.micro"
  key_name      = var.key_pair_name

  # Cấu hình network interface để gán Security Group và Public IP
  network_interfaces {
    associate_public_ip_address = true
    security_groups             = [aws_security_group.sg_ec2.id]
  }

  # User Data: Cài đặt Docker (Mã hóa base64 bắt buộc cho Launch Template)
  user_data = base64encode(<<-EOF
              #!/bin/bash
              yum update -y
              yum install -y docker
              systemctl start docker
              systemctl enable docker
              usermod -aG docker ec2-user
              EOF
  )

  # Gán Tag cho instance được sinh ra
  tag_specifications {
    resource_type = "instance"
    tags = {
      Name = "Task-Tracker-ASG-Node"
    }
  }

  lifecycle {
    create_before_destroy = true
  }
}

# 3. Tạo Auto Scaling Group (ASG)
resource "aws_autoscaling_group" "app_asg" {
  name                = "prod-task-tracker-asg"
  vpc_zone_identifier = data.aws_subnets.default.ids # Chạy trên các subnet mặc định

  # Cấu hình số lượng instance
  min_size         = 1
  max_size         = 3
  desired_capacity = 1

  # Tự động đăng ký instance mới vào Load Balancer Target Group
  target_group_arns = [aws_lb_target_group.tg.arn]

  # Sử dụng Launch Template đã tạo ở trên
  launch_template {
    id      = aws_launch_template.app_lt.id
    version = "$Latest"
  }

  # Sử dụng health check của ELB để biết instance có sống hay không
  health_check_type         = "ELB"
  health_check_grace_period = 300

  tag {
    key                 = "Name"
    value               = "Task-Tracker-ASG-Instance"
    propagate_at_launch = true
  }
}

# 4. Policy: Tự động scale khi CPU > 70%
resource "aws_autoscaling_policy" "cpu_tracking" {
  name                   = "cpu-tracking-policy"
  autoscaling_group_name = aws_autoscaling_group.app_asg.name
  policy_type            = "TargetTrackingScaling"

  target_tracking_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ASGAverageCPUUtilization"
    }
    target_value = 70.0
  }
}