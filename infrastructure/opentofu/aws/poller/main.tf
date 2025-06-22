resource "aws_lambda_function" "seismicity" {
  function_name = "seismicity-function"
  role          = var.lambda_role_arn
  handler       = "handler.handler"
  runtime       = "python3.9"

  s3_bucket = var.s3_bucket_name
  s3_key    = "function.zip"

  environment {
    variables = {
      S3_BUCKET     = var.s3_bucket_name
      S3_KEY_PREFIX = "events/"
      AWS_REGION    = var.region
    }
  }
}
