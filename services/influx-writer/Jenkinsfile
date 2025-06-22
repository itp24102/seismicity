provider "aws" {
  region = var.region
}

resource "aws_iam_role" "influx_lambda_role" {
  name = "seismicity-influx-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action = "sts:AssumeRole",
      Principal = { Service = "lambda.amazonaws.com" },
      Effect = "Allow"
    }]
  })
}

resource "aws_iam_role_policy" "influx_lambda_policy" {
  name = "influx-logging-policy"
  role = aws_iam_role.influx_lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_lambda_function" "influx_writer" {
  function_name = "influx-writer"
  role          = aws_iam_role.influx_lambda_role.arn
  handler       = "influx_writer.handler"
  runtime       = "python3.9"

  s3_bucket = var.s3_bucket_name
  s3_key    = "influx_writer.zip"

  environment {
    variables = {
      INFLUX_URL    = var.influx_url
      INFLUX_TOKEN  = var.influx_token
      INFLUX_ORG    = "seismicity"
      INFLUX_BUCKET = "seismicity"
    }
  }
}
