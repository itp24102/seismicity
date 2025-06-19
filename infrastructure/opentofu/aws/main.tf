provider "aws" {
  region = var.region
}

resource "aws_s3_bucket" "seismicity_bucket" {
  bucket = var.s3_bucket_name

  tags = {
    Name = "seismicity-app-bucket"
    Environment = "development"
  }
}

resource "aws_iam_role" "lambda_role" {
  name = "seismicity-lambda-role"

  assume_role_policy = jsonencode({  
    Version = "2012-10-17",
    Statement = [{
      Action = "sts:AssumeRole",
      Principal = { Service = "lambda.amazonaws.com" },
      Effect = "Allow"
    }]
  })
}

resource "aws_iam_role_policy" "lambda_policy" {
  name = "seismicity-lambda-policy"
  role  = aws_iam_role.lambda_role.id

  policy = jsonencode({  
    Version = "2012-10-17",
    Statement = [{
      Action = [
        "s3:*"
      ],
      Effect = "Allow",
      Resource = aws_s3_bucket.seismicity_bucket.arn
    }]
  })
}

resource "aws_lambda_function" "seismicity" {
  function_name = "seismicity-function"
  role          = aws_iam_role.lambda_role.arn
  handler       = "handler.handler"
  runtime       = "python3.9"

  s3_bucket        = aws_s3_bucket.seismicity_bucket.bucket 
  s3_key           = "function.zip"
  source_code_hash = filebase64sha256("function.zip")

  environment {
    variables = {
      S3_BUCKET     = aws_s3_bucket.seismicity_bucket.bucket
      S3_KEY_PREFIX = "events/"
      AWS_REGION    = var.region
    }
  }
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
      INFLUX_URL    = var.influx_url       # π.χ. "http://influxdb.monitoring.svc.cluster.local:8086"
      INFLUX_TOKEN  = var.influx_token     # token από InfluxDB
      INFLUX_ORG    = "seismicity"
      INFLUX_BUCKET = "seismicity"
    }
  }
}
