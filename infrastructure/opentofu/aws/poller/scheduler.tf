resource "aws_cloudwatch_event_rule" "poller_schedule" {
  name                = "poller-schedule"
  description         = "Trigger seismicity-function every 5 minutes"
  schedule_expression = "rate(5 minutes)"
  is_enabled          = true
}

resource "aws_cloudwatch_event_target" "poller_lambda_target" {
  rule      = aws_cloudwatch_event_rule.poller_schedule.name
  target_id = "seismicity-function-target"
  arn       = aws_lambda_function.seismicity.arn
}
