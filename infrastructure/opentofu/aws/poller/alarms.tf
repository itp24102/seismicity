resource "aws_cloudwatch_metric_alarm" "poller_invocations" {
  alarm_name          = "poller-no-execution"
  alarm_description   = "Poller Lambda did not run in the last 5 minutes (SLA breach risk)"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Invocations"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 1

  dimensions = {
    FunctionName = aws_lambda_function.seismicity.function_name
  }

  treat_missing_data = "breaching"
  actions_enabled    = true
}
