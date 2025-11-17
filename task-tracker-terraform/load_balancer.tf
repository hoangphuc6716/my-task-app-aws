# File: load_balancer.tf

resource "aws_lb" "alb" {
  name               = "prod-task-tracker-lb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.sg_lb.id]
  subnets            = data.aws_subnets.default.ids

  tags = {
    Name = "Task-Tracker-LB-Prod"
  }
}

resource "aws_lb_target_group" "tg" {
  name     = "prod-task-tracker-tg"
  port     = 80
  protocol = "HTTP"
  vpc_id   = data.aws_vpc.default.id

  health_check {
    path                = "/health" # Đảm bảo app của bạn có endpoint này, hoặc đổi thành "/"
    protocol            = "HTTP"
    port                = "traffic-port"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 30
    matcher             = "200"
  }
}

# ĐÃ XÓA RESOURCE: aws_lb_target_group_attachment (ASG sẽ tự động attach)

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.alb.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.tg.arn
  }
}