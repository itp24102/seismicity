provider "aws" {
  region = var.region
}

resource "aws_iam_role" "poller_lambda_role" {
  name = "seismicity-poller-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action = "sts:AssumeRole",
      Principal = { Service = "lambda.amazonaws.com" },
      Effect = "Allow"
    }]
  })
}

resource "aws_iam_role_policy" "poller_lambda_policy" {
  name = "poller-s3-policy"
  role = aws_iam_role.poller_lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action = [
        "s3:*"
      ],
      Effect = "Allow",
      Resource = "*"
    }]
  })
}

resource "aws_lambda_function" "poller" {
  function_name = "seismicity-function"
  role          = aws_iam_role.poller_lambda_role.arn
  handler       = "handler.handler"
  runtime       = "python3.9"

  s3_bucket        = var.s3_bucket
  s3_key           = "function.zip"
  source_code_hash = filebase64sha256("function.zip")

  environment {
    variables = {
      S3_BUCKET     = var.s3_bucket
      S3_KEY_PREFIX = "events/"
      AWS_REGION    = var.region
    }
  }
}
