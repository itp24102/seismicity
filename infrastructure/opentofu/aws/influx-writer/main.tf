provider "aws" {
  region = var.region
}

resource "aws_iam_role" "lambda_role" {
  name = "influx-writer-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action = "sts:AssumeRole",
      Principal = { Service = "lambda.amazonaws.com" },
      Effect = "Allow"
    }]
  })
}

resource "aws_lambda_function" "influx_writer" {
  function_name = "influx-writer"
  handler       = "influx_writer.handler"
  runtime       = "python3.9"
  role          = aws_iam_role.lambda_role.arn

  filename         = "influx_writer.zip"
  source_code_hash = filebase64sha256("influx_writer.zip")

  environment {
    variables = {
      INFLUX_URL    = var.influx_url
      INFLUX_TOKEN  = var.influx_token
      INFLUX_ORG    = var.influx_org
      INFLUX_BUCKET = var.influx_bucket
    }
  }
}