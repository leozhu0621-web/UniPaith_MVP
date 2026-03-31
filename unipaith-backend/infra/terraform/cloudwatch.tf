# Budget alarms to prevent runaway GPU costs

resource "aws_sns_topic" "budget_alerts" {
  name = "${var.project}-budget-alerts"
}

resource "aws_sns_topic_subscription" "email" {
  topic_arn = aws_sns_topic.budget_alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# Alarm: estimated charges exceed $1,500
resource "aws_cloudwatch_metric_alarm" "budget_warning" {
  alarm_name          = "${var.project}-budget-warning"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "EstimatedCharges"
  namespace           = "AWS/Billing"
  period              = 21600  # 6 hours
  statistic           = "Maximum"
  threshold           = 1500
  alarm_description   = "GPU spending approaching budget cap"
  alarm_actions       = [aws_sns_topic.budget_alerts.arn]

  dimensions = {
    Currency = "USD"
  }
}

# Alarm: estimated charges exceed $2,000 (hard cap)
resource "aws_cloudwatch_metric_alarm" "budget_critical" {
  alarm_name          = "${var.project}-budget-critical"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "EstimatedCharges"
  namespace           = "AWS/Billing"
  period              = 21600
  statistic           = "Maximum"
  threshold           = 2000
  alarm_description   = "GPU spending exceeded budget cap!"
  alarm_actions       = [aws_sns_topic.budget_alerts.arn]

  dimensions = {
    Currency = "USD"
  }
}
