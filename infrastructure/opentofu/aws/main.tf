provider "aws" {
  region = var.region
}

data "aws_iam_role" "lambda_role" {
  name = "seismicity-lambda-role"
}

data "aws_s3_bucket" "seismicity_bucket" {
  bucket = var.s3_bucket_name
}

resource "aws_lambda_function" "seismicity" {
  function_name = "seismicity-function"
  role          = data.aws_iam_role.lambda_role.arn
  handler       = "handler.handler"
  runtime       = "python3.9"

  s3_bucket        = data.aws_s3_bucket.seismicity_bucket.id
  s3_key           = "function.zip"
  source_code_hash = filebase64sha256("function.zip")

  environment {
    variables = {
      S3_BUCKET     = data.aws_s3_bucket.seismicity_bucket.id
      S3_KEY_PREFIX = "events/"
      AWS_REGION    = var.region
    }
  }
}

resource "aws_lambda_function" "influx_writer" {
  function_name = "influx-writer"
  handler       = "influx_writer.handler"
  runtime       = "python3.9"
  role          = data.aws_iam_role.lambda_role.arn

  filename         = "influx_writer.zip"
  source_code_hash = filebase64sha256("influx_writer.zip")

  environment {
    variables = {
      INFLUX_URL    = var.influx_url
      INFLUX_TOKEN  = var.influx_token
      INFLUX_ORG    = "seismicity"
      INFLUX_BUCKET = "seismicity"
    }
  }
}
